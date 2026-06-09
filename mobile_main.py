"""
Distiller 移动版 — Flask 后端 + 单文件打包
手机端访问: http://localhost:8888
"""

import os
import sys
import json
import threading
import webbrowser

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')

# 初始化数据库
sys.path.insert(0, BASE_DIR)
from backend.database import init_db
init_db()

# 导入所有后端模块（注册功能）
import backend.config
import backend.llm_client
import backend.knowledge_base
import backend.distillation
import backend.web_search
import backend.skill_manager
import backend.persona_template


# ===== 通用 API 路由 —— 将 Eel 函数自动暴露为 HTTP API =====

import backend.config as cfg
import backend.knowledge_base as kb
import backend.llm_client as llm
import backend.distillation as dist
import backend.web_search as ws
import backend.skill_manager as sk
import backend.persona_template as pt


def _api_response(result):
    """包装返回值为 JSON"""
    if result is None:
        return jsonify({'ok': False, 'error': '无返回'})
    return jsonify(result)


# 配置
app.add_url_rule('/api/hello', 'hello', lambda: jsonify('Distiller backend is running!'))
app.add_url_rule('/api/get_config', 'get_config', lambda: jsonify(cfg.load_config()))
app.add_url_rule('/api/set_api_key', 'set_api_key', lambda: _api_response(cfg.set_api_key(request.json.get('key', ''))), methods=['POST'])
app.add_url_rule('/api/test_api_connection', 'test_api_connection', lambda: _api_response(llm.test_api_connection()))

# 对话
@app.route('/api/send_message', methods=['POST'])
def api_send_message():
    data = request.json or {}
    return _api_response(llm.send_message(
        data.get('message', ''),
        data.get('history', []),
        data.get('kb_id'),
        data.get('skill_id'),
    ))


@app.route('/api/send_message_stream', methods=['POST'])
def api_send_message_stream():
    data = request.json or {}
    # 非流式回退（移动端用）
    result = llm.send_message(
        data.get('message', ''),
        data.get('history', []),
        data.get('kb_id'),
        data.get('skill_id'),
    )
    return _api_response(result)


# 知识库
app.add_url_rule('/api/list_knowledge_bases', 'list_knowledge_bases', lambda: jsonify(kb.list_knowledge_bases()))
app.add_url_rule('/api/get_kb_documents', 'get_kb_documents', lambda: jsonify(kb.get_kb_documents(request.args.get('kb_id', 1))))
app.add_url_rule('/api/get_kb_stats', 'get_kb_stats', lambda: jsonify(kb.get_kb_stats(request.args.get('kb_id', 1))))
app.add_url_rule('/api/rename_knowledge_base', 'rename_knowledge_base', lambda: _api_response(kb.rename_knowledge_base(request.json.get('kb_id'), request.json.get('name', ''))), methods=['POST'])
app.add_url_rule('/api/delete_knowledge_base', 'delete_knowledge_base', lambda: _api_response(kb.delete_knowledge_base(request.json.get('kb_id'))), methods=['POST'])
app.add_url_rule('/api/create_knowledge_base', 'create_knowledge_base', lambda: _api_response(kb.create_knowledge_base(request.json.get('name', ''), request.json.get('description', ''))), methods=['POST'])
app.add_url_rule('/api/ingest_text', 'ingest_text', lambda: _api_response(kb.ingest_text(request.json.get('kb_id'), request.json.get('title', ''), request.json.get('text', ''))), methods=['POST'])
app.add_url_rule('/api/ingest_file', 'ingest_file', lambda: _api_response(kb.ingest_file(request.json.get('kb_id'), request.json.get('filepath', ''), request.json.get('title'))), methods=['POST'])
app.add_url_rule('/api/select_file_dialog', 'select_file_dialog', lambda: jsonify({'ok': False, 'error': '手机端不支持文件选择器，请使用粘贴文本功能'}))
app.add_url_rule('/api/search_knowledge_base', 'search_knowledge_base', lambda: jsonify(kb.search_knowledge_base(request.args.get('kb_id', 1), request.args.get('query', ''), int(request.args.get('k', 5)))))
app.add_url_rule('/api/delete_document', 'delete_document', lambda: _api_response(kb.delete_document(request.json.get('doc_id'))), methods=['POST'])

# 蒸馏
app.add_url_rule('/api/get_distillation_modes', 'get_distillation_modes', lambda: jsonify(dist.get_distillation_modes()))
app.add_url_rule('/api/distill', 'distill', lambda: _api_response(dist.distill(request.json.get('kb_id'), request.json.get('mode', ''), request.json.get('instruction', ''))), methods=['POST'])
app.add_url_rule('/api/distill_generate', 'distill_generate', lambda: _api_response(dist.distill_generate(request.json.get('kb_id'), request.json.get('style_report', ''), request.json.get('request', ''))), methods=['POST'])

# 搜索
app.add_url_rule('/api/web_search', 'web_search', lambda: jsonify(ws.web_search(request.args.get('query', ''), int(request.args.get('max', 10)))))
app.add_url_rule('/api/fetch_and_ingest_urls', 'fetch_and_ingest_urls', lambda: _api_response(ws.fetch_and_ingest_urls(request.json.get('kb_id'), request.json.get('urls', []))), methods=['POST'])

# Skills
app.add_url_rule('/api/list_skills', 'list_skills', lambda: jsonify(sk.list_skills()))
app.add_url_rule('/api/create_skill', 'create_skill', lambda: _api_response(sk.create_skill(request.json.get('name'), request.json.get('type'), request.json.get('system_prompt'), request.json.get('description', ''))), methods=['POST'])
app.add_url_rule('/api/update_skill', 'update_skill', lambda: _api_response(sk.update_skill(request.json.get('id'), request.json.get('name'), request.json.get('system_prompt'), request.json.get('description', ''))), methods=['POST'])
app.add_url_rule('/api/delete_skill', 'delete_skill', lambda: _api_response(sk.delete_skill(request.json.get('id'))), methods=['POST'])
app.add_url_rule('/api/get_skill', 'get_skill', lambda: jsonify(sk.get_skill(int(request.args.get('id', 0)))))
app.add_url_rule('/api/save_distill_as_skill', 'save_distill_as_skill', lambda: _api_response(sk.save_distill_as_skill(request.json.get('name'), request.json.get('report'), request.json.get('mode_name', ''))), methods=['POST'])

# 模板
app.add_url_rule('/api/get_persona_template', 'get_persona_template', lambda: pt.get_template())


# ===== 前端页面 =====

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index_mobile.html')


@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(FRONTEND_DIR, path)


if __name__ == '__main__':
    print('')
    print('  Distiller 移动版已启动')
    print('  手机浏览器打开: http://localhost:8888')
    print('')
    threading.Timer(1.5, lambda: webbrowser.open('http://localhost:8888')).start()
    app.run(host='0.0.0.0', port=8888, debug=False)
