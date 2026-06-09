"""DeepSeek API 调用封装 — OpenAI 兼容协议 + RAG + Streaming"""

import eel
from openai import OpenAI

from backend.config import get_api_key, get_setting


def _get_client():
    api_key = get_api_key()
    base_url = get_setting('deepseek_base_url')
    timeout = get_setting('http_timeout')
    if not api_key:
        raise ValueError('请先在设置中配置 DeepSeek API Key')
    return OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)


def _get_model():
    return get_setting('deepseek_model')


@eel.expose
def test_api_connection():
    """测试 API 连接 — 用极简请求验证 key 和网络是否正常"""
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=_get_model(),
            messages=[{'role': 'user', 'content': '回复 OK'}],
            max_tokens=5,
            timeout=15,
        )
        reply = response.choices[0].message.content
        return {'ok': True, 'reply': reply}
    except Exception as e:
        msg = str(e)
        if '401' in msg or 'Unauthorized' in msg or 'Authentication' in msg:
            return {'ok': False, 'error': 'API Key 无效，请检查是否正确（格式通常为 sk-xxxxxxxx）'}
        if '404' in msg or 'Not Found' in msg:
            return {'ok': False, 'error': f'模型 "{_get_model()}" 不存在，请尝试其他模型'}
        if 'timeout' in msg.lower() or 'timed out' in msg.lower():
            return {'ok': False, 'error': '连接超时，请检查网络或 API 地址是否正确'}
        if 'Connection' in msg or 'connect' in msg.lower():
            return {'ok': False, 'error': f'无法连接到 DeepSeek API，请检查网络或代理设置。\n详情: {msg}'}
        return {'ok': False, 'error': f'连接失败: {msg}'}


@eel.expose
def send_message(message, history=None, kb_id=None, skill_id=None):
    """非流式发送消息"""
    try:
        client = _get_client()
        if history is None:
            history = []

        system_prompt = _build_system_prompt(kb_id, message, skill_id)

        messages = [{'role': 'system', 'content': system_prompt}]
        messages.extend(history)
        messages.append({'role': 'user', 'content': message})

        response = client.chat.completions.create(
            model=_get_model(),
            messages=messages,
            max_tokens=2048,
            temperature=0.6,
            timeout=get_setting('http_timeout'),
        )
        reply = response.choices[0].message.content
        return {'ok': True, 'reply': reply}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


@eel.expose
def send_message_stream(message, history=None, kb_id=None, skill_id=None):
    """流式发送消息，逐 token 推送至前端 onStreamToken(token, is_first, is_done)"""
    try:
        client = _get_client()
        if history is None:
            history = []

        system_prompt = _build_system_prompt(kb_id, message, skill_id)

        messages = [{'role': 'system', 'content': system_prompt}]
        messages.extend(history)
        messages.append({'role': 'user', 'content': message})

        stream = client.chat.completions.create(
            model=_get_model(),
            messages=messages,
            max_tokens=2048,
            temperature=0.6,
            stream=True,
            timeout=get_setting('http_timeout'),
        )

        is_first = True
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                eel.onStreamToken(token, is_first, False)()
                is_first = False

        eel.onStreamToken('', False, True)()
        return {'ok': True}

    except Exception as e:
        # 流式失败，尝试非流式降级
        try:
            response = client.chat.completions.create(
                model=_get_model(),
                messages=messages,
                max_tokens=2048,
                temperature=0.6,
                timeout=get_setting('http_timeout'),
            )
            reply = response.choices[0].message.content
            eel.onStreamToken(reply, True, True)()
            return {'ok': True}
        except Exception:
            eel.onStreamToken(f'\n\n❌ 错误: {str(e)}', False, True)()
            return {'ok': False, 'error': str(e)}


def _build_system_prompt(kb_id, message, skill_id=None):
    from backend.skill_manager import get_skill_prompt, get_skill_type

    skill_type = get_skill_type(skill_id) if skill_id else None
    skill_prompt = get_skill_prompt(skill_id) if skill_id else ''

    # 角色模式：纯沉浸式扮演，不提 AI 身份和资料
    if skill_type == 'persona' and skill_prompt:
        system_prompt = skill_prompt
        # 角色模式也检索资料作为背景知识，但不暴露给用户
        if kb_id and int(kb_id) > 0:
            try:
                from backend.knowledge_base import search_knowledge_base
                result = search_knowledge_base(kb_id, message, k=5)
                if result['ok'] and result['results']:
                    parts = []
                    for r in result['results']:
                        parts.append(r['content'])
                    context = '\n\n'.join(parts)
                    system_prompt += f'\n\n【背景知识，不要提及来源，直接当作自己知道的内容使用】\n{context}'
            except Exception:
                pass
        return system_prompt

    # 模板模式：注入分析视角 + RAG
    if skill_type == 'template' and skill_prompt:
        system_prompt = '你是 Distiller，一款知识蒸馏助手。\n\n' + skill_prompt
    else:
        system_prompt = '你是 Distiller 知识助手。用中文回答，像跟朋友聊天一样自然。回应简洁有力，不用"当然可以""很高兴为你"这类客套话。用户问什么就答什么，不要给自己加戏。'

    # RAG：在模板或默认模式下检索资料
    if kb_id and int(kb_id) > 0:
        try:
            from backend.knowledge_base import search_knowledge_base
            result = search_knowledge_base(kb_id, message, k=5)
            if result['ok'] and result['results']:
                parts = []
                for r in result['results']:
                    parts.append(f'【来源：{r["metadata"].get("title", "未知")}】\n{r["content"]}')
                context = '\n\n---\n\n'.join(parts)
                system_prompt += '\n\n以下是从知识库中检索到的相关资料，请基于这些资料回答：\n\n' + context
        except Exception:
            pass

    return system_prompt
