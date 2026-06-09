"""蒸馏引擎 — Prompt Chain + 结构化方法论报告"""

import eel
from openai import OpenAI

from backend.config import get_api_key, get_setting
from backend.knowledge_base import search_knowledge_base

# ---------- 蒸馏 Prompt 模板 ----------

PERSONA_SYSTEM = """你是一位顶级的「人物方法论蒸馏师」。你的任务是从提供的资料中，系统性地提炼出目标人物的做事方法论、思维模式和行动风格。

请按以下结构输出报告（Markdown 格式）：

## 🎯 核心行事原则
- 列出 3-5 条该人物反复体现的核心原则
- 每条原则配一句资料中的具体事例

## 🧠 决策模式
- 分析该人物做决策的框架（例如：第一性原理、数据驱动、直觉判断等）
- 说明在什么情况下会如何决策

## 💬 沟通风格
- 概括该人物的沟通特征（直接/委婉、简洁/详尽、理性/感性）
- 典型表达方式或标志性语言

## 🔧 执行方法论
- 该人物如何将想法落地的方法论
- 团队管理、资源调配方面的特点

## ⚠️ 风险偏好
- 分析该人物的风险态度和应对策略

## 📋 可复用的行动清单
- 将该人物的方法论转化为用户可直接使用的 5-10 条具体行动建议
"""

DOMAIN_SYSTEM = """你是一位顶级的「领域知识蒸馏师」。你的任务是从提供的专业资料中，提炼出该领域的核心知识体系。

请按以下结构输出报告（Markdown 格式）：

## 📖 核心概念体系
- 列出该领域最关键的 5-10 个概念及其定义
- 概念之间的层级或关联关系

## 🔗 关键原理/定律
- 该领域公认的核心原理或规律
- 每个原理的简要解释和应用场景

## 🗺️ 知识框架
- 该领域的整体知识结构（可以用层级列表表示）
- 学习路径建议：从入门到精通的顺序

## ⚡ 常见误区
- 该领域新手容易犯的 3-5 个错误
- 正确理解是什么

## 📊 实用要点速查
- 列出该领域最常用的公式/数据/规则（如适用）
- 便于快速查阅的关键结论
"""

STYLE_SYSTEM = """你是一位顶级的「风格特征蒸馏师」。你的任务是从创作者的作品中提炼其独特的创作风格特征，以便能够模仿和生成类似风格的内容。

请按以下结构输出报告（Markdown 格式）：

## 🎨 词汇偏好
- 高频使用的独特词汇（按类别分组）
- 标志性的形容词、动词、名词选择倾向

## 🌌 意象体系
- 反复出现的意象和隐喻
- 意象之间的组合模式

## 🎵 节奏与结构
- 作品的节奏特点（句式长短、段落结构）
- 组织内容的结构习惯

## 🖊️ 修辞手法
- 常用的修辞技巧（比喻、排比、对比等）
- 每种手法的典型示例

## 🎭 情感基调
- 作品整体传达的情感氛围
- 情感表达的方式（含蓄/直白、温暖/冷峻等）

## ✍️ 风格生成指南
- 将该风格转化为可操作的创作指南
- 包含句式模板、常用词汇库、意象组合建议
"""

CHAT_STYLE_SYSTEM = """你是一位顶级的「聊天方式蒸馏师」。你的任务是从聊天记录中，极度细致地提炼出一个人的聊天风格，目标是让 AI 能够完美模仿这个人的说话方式。

请按以下结构输出报告（Markdown 格式）：

## 🗣️ 口癖与高频词
- 列出这个人最常说的口头禅、语气词（如"说实话""就是说""嗯""哈哈哈"）
- 每个口癖的典型使用场景
- 高频使用的连接词、转折词

## 😊 性格特征在聊天中的体现
- 从聊天中反推这个人的性格（外向/内向、主动/被动、理性/感性）
- 具体表现：回复速度倾向、消息长度、是否喜欢用表情
- 情绪表达方式：直白还是含蓄，会不会主动分享感受

## 💬 句式与表达习惯
- 句子长度偏好（短句/长句/混合）
- 喜欢用陈述句/疑问句/感叹句的比例
- 习惯用第几人称（"我觉得"/"你会觉得"/"大家都会"）
- 是否喜欢用反问、设问

## 😂 幽默与语气
- 幽默风格（冷幽默/自嘲/调侃/网络梗）
- 语气词使用频率和类型（呢/吧/啊/哦/嘛）
- 标点习惯（喜欢用感叹号/省略号/表情符号）

## 📱 聊天习惯细节
- 如何开启话题（直接/问候/表情/分享链接）
- 如何结束对话（"先忙了"/表情/突然消失）
- 会不会追问、会不会主动换话题
- 对沉默的反应方式

## 🎯 一对一模仿指南
- 用 3-5 句话精确描述"如何像这个人一样聊天"
- 如果要用 200 字以内写一个 system prompt 让 AI 成为这个人，应该怎么写
- 给出 5 个典型对话示例（包含这个人的代表性回复）"""

CHAT_GENERATE_SYSTEM = """你正在进行角色扮演聊天。你不是 AI，你就是这个人本人。

【你的身份】
{report}

【聊天规则】
- 完全按这个人的口癖、语气、句式说话
- 用口语，不要用 Markdown
- 像真人聊天一样，可以"嗯"、"哈哈"、"等一下我想想"
- 不要回答太长，真人聊天一般几句到一小段
- 可以用适当的 emoji 或表情符号（如果这个人平时会用）
- 绝对不会说"作为AI"、"根据资料"、"基于分析"这类话
- 被问到"你是谁"就说自己是谁（这个人的身份），完全自然"""



def _get_client():
    api_key = get_api_key()
    base_url = get_setting('deepseek_base_url')
    if not api_key:
        raise ValueError('请先在设置中配置 DeepSeek API Key')
    return OpenAI(api_key=api_key, base_url=base_url)


def _get_model():
    return get_setting('deepseek_model')


# ---------- 蒸馏模式配置 ----------

MODES = {
    'persona': {
        'name': '人物方法论',
        'icon': '👤',
        'system': PERSONA_SYSTEM,
        'user_prompt': '请基于提供的资料，蒸馏出该人物的做事方法论。要求深度分析，给出可操作的结论。',
    },
    'domain': {
        'name': '领域专业知识',
        'icon': '📚',
        'system': DOMAIN_SYSTEM,
        'user_prompt': '请基于提供的资料，蒸馏出该领域的核心知识体系。要求系统全面，便于学习和查阅。',
    },
    'style': {
        'name': '风格特征',
        'icon': '🎨',
        'system': STYLE_SYSTEM,
        'user_prompt': '请基于提供的作品资料，蒸馏出该创作者的风格特征。要求具体细致，能够指导风格模仿。',
    },
    'chat_style': {
        'name': '聊天方式',
        'icon': '💬',
        'system': CHAT_STYLE_SYSTEM,
        'user_prompt': '请基于提供的聊天记录，极度细致地蒸馏出这个人的聊天方式——口癖、语气、句式、性格、幽默风格等。目标是让 AI 能够完美模仿这个人聊天。',
    },
}


@eel.expose
def get_distillation_modes():
    """返回可用的蒸馏模式列表"""
    return [{'key': k, 'name': v['name'], 'icon': v['icon']} for k, v in MODES.items()]


@eel.expose
def distill(kb_id, mode, custom_instruction=''):
    """执行蒸馏——从知识库检索资料，生成结构化方法论报告"""
    kb_id = int(kb_id)
    if mode not in MODES:
        return {'ok': False, 'error': f'未知蒸馏模式: {mode}'}

    mode_config = MODES[mode]

    # 步骤 1：从知识库广泛检索资料
    search_queries = _get_search_queries(mode)
    all_chunks = []
    seen = set()

    for query in search_queries:
        result = search_knowledge_base(kb_id, query, k=8)
        if result['ok']:
            for r in result['results']:
                if r['id'] not in seen:
                    seen.add(r['id'])
                    all_chunks.append(r)

    if not all_chunks:
        return {'ok': False, 'error': '知识库为空，请先录入资料后再蒸馏'}

    # 步骤 2：构建蒸馏上下文
    context_parts = []
    for r in all_chunks[:30]:  # 最多取 30 个相关块，避免 token 超限
        title = r['metadata'].get('title', '未知')
        context_parts.append(f'【来源：{title}】\n{r["content"]}')

    context = '\n\n---\n\n'.join(context_parts)

    user_message = mode_config['user_prompt']
    if custom_instruction:
        user_message += f'\n\n用户的额外要求：{custom_instruction}'

    user_message += f'\n\n---\n\n以下是要分析的资料：\n\n{context}'

    # 步骤 3：调用 LLM 生成蒸馏报告
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=_get_model(),
            messages=[
                {'role': 'system', 'content': mode_config['system']},
                {'role': 'user', 'content': user_message},
            ],
            max_tokens=4096,
            temperature=0.5,  # 偏低温度保证分析严谨
        )
        report = response.choices[0].message.content
        return {
            'ok': True,
            'report': report,
            'mode': mode,
            'mode_name': mode_config['name'],
            'sources_count': len(all_chunks),
        }
    except Exception as e:
        return {'ok': False, 'error': f'蒸馏失败: {str(e)}'}


@eel.expose
def distill_generate(kb_id, style_report, request):
    """基于蒸馏出的风格报告 + 用户要求，生成符合风格的新内容"""
    kb_id = int(kb_id)
    if not style_report or not request:
        return {'ok': False, 'error': '缺少风格报告或生成要求'}

    # 检索资料中的示例素材
    result = search_knowledge_base(kb_id, request, k=6)
    examples = ''
    if result['ok'] and result['results']:
        parts = []
        for r in result['results'][:6]:
            parts.append(r['content'])
        examples = '\n\n---\n\n'.join(parts)

    system_prompt = f"""你是一位精通风格模仿的创作助手。以下是对某创作者风格的深度分析报告：

{style_report}

请严格基于以上风格分析，根据用户的要求进行创作。
创作原则：
1. 忠实还原风格特征（用词、意象、节奏、修辞）
2. 内容符合用户的主题要求
3. 标注创作中运用了哪些风格特征
4. 最后附上简要的"风格运用说明"解释你的创作选择"""

    user_message = f'创作要求：{request}'
    if examples:
        user_message += f'\n\n以下是该创作者的原作片段供参考风格：\n\n{examples}'

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=_get_model(),
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message},
            ],
            max_tokens=4096,
            temperature=0.8,  # 创作需要一定随机性
        )
        generated = response.choices[0].message.content
        return {'ok': True, 'generated': generated}
    except Exception as e:
        return {'ok': False, 'error': f'生成失败: {str(e)}'}


def _get_search_queries(mode):
    """根据蒸馏模式生成多角度检索查询"""
    if mode == 'persona':
        return [
            '决策方式 思维模式 原则',
            '团队管理 领导风格 执行方法',
            '沟通方式 表达能力 谈判策略',
            '风险 挑战 应对策略 失败',
            '创新 突破 独特做法 方法论',
        ]
    elif mode == 'domain':
        return [
            '核心概念 定义 基本原理',
            '知识框架 体系 结构',
            '关键原理 定律 规律',
            '常见误区 注意事项 实践',
            '应用 案例 实际操作',
        ]
    elif mode == 'style':
        return [
            '意象 比喻 象征 画面',
            '词汇 用词 语言风格 句式',
            '节奏 结构 段落 组织',
            '情感 基调 氛围 色彩',
            '修辞 手法 技巧 表达',
        ]
    elif mode == 'chat_style':
        return [
            '口头禅 语气词 习惯 高频词',
            '回复方式 说话风格 句式',
            '情绪 表情 语气 态度',
            '性格 主动 被动 内向 外向',
            '幽默 玩笑 调侃 认真',
        ]
    return ['']  # fallback
