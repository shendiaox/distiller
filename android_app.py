"""
Distiller Android — 极简 WebView + Flask
"""

import os
import threading

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from flask import Flask, jsonify, request, send_from_directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')

import sys
sys.path.insert(0, BASE_DIR)
from backend.database import init_db
init_db()

import backend.knowledge_base as kb
import backend.llm_client as llm
import backend.distillation as dist
import backend.web_search as ws
import backend.skill_manager as sk
import backend.persona_template as pt
import backend.config as cfg


def _ok(r): return jsonify(r if r is not None else {'ok': False})


# 注册所有 API 路由
app.add_url_rule('/api/hello', 'hello', lambda: jsonify('Distiller Mobile'))
app.add_url_rule('/api/get_config', 'cfg', lambda: jsonify(cfg.load_config()))
app.add_url_rule('/api/set_api_key', 'set_key', lambda: _ok(cfg.set_api_key((request.json or {}).get('key', ''))), methods=['POST'])
app.add_url_rule('/api/test_api_connection', 'test', lambda: _ok(llm.test_api_connection()))


@app.route('/api/send_message', methods=['POST'])
def api_chat():
    d = request.json or {}
    return _ok(llm.send_message(d.get('message', ''), d.get('history', []), d.get('kb_id'), d.get('skill_id')))


@app.route('/api/list_knowledge_bases')
def api_kb(): return jsonify(kb.list_knowledge_bases())


@app.route('/api/create_knowledge_base', methods=['POST'])
def api_ckb():
    d = request.json or {}; return _ok(kb.create_knowledge_base(d.get('name', ''), d.get('description', '')))


@app.route('/api/ingest_text', methods=['POST'])
def api_ingest():
    d = request.json or {}; return _ok(kb.ingest_text(d.get('kb_id'), d.get('title', ''), d.get('text', '')))


@app.route('/api/search_knowledge_base')
def api_search():
    return jsonify(kb.search_knowledge_base(request.args.get('kb_id', 1), request.args.get('query', ''), int(request.args.get('k', 5))))


@app.route('/api/get_kb_documents')
def api_docs(): return jsonify(kb.get_kb_documents(request.args.get('kb_id', 1)))


@app.route('/api/get_kb_stats')
def api_stats(): return jsonify(kb.get_kb_stats(request.args.get('kb_id', 1)))


@app.route('/api/rename_knowledge_base', methods=['POST'])
def api_rkb():
    d = request.json or {}; return _ok(kb.rename_knowledge_base(d.get('kb_id'), d.get('name', '')))


@app.route('/api/delete_knowledge_base', methods=['POST'])
def api_dkb():
    d = request.json or {}; return _ok(kb.delete_knowledge_base(d.get('kb_id')))


@app.route('/api/delete_document', methods=['POST'])
def api_ddoc():
    d = request.json or {}; return _ok(kb.delete_document(d.get('doc_id')))


@app.route('/api/get_distillation_modes')
def api_modes(): return jsonify(dist.get_distillation_modes())


@app.route('/api/distill', methods=['POST'])
def api_distill():
    d = request.json or {}; return _ok(dist.distill(d.get('kb_id'), d.get('mode', ''), d.get('instruction', '')))


@app.route('/api/distill_generate', methods=['POST'])
def api_gen():
    d = request.json or {}; return _ok(dist.distill_generate(d.get('kb_id'), d.get('style_report', ''), d.get('request', '')))


@app.route('/api/web_search')
def api_ws():
    return jsonify(ws.web_search(request.args.get('query', ''), int(request.args.get('max', 10))))


@app.route('/api/fetch_and_ingest_urls', methods=['POST'])
def api_fetch():
    d = request.json or {}; return _ok(ws.fetch_and_ingest_urls(d.get('kb_id'), d.get('urls', [])))


@app.route('/api/list_skills')
def api_lsk(): return jsonify(sk.list_skills())


@app.route('/api/create_skill', methods=['POST'])
def api_csk():
    d = request.json or {}; return _ok(sk.create_skill(d.get('name'), d.get('type'), d.get('system_prompt'), d.get('description', '')))


@app.route('/api/save_distill_as_skill', methods=['POST'])
def api_ssk():
    d = request.json or {}; return _ok(sk.save_distill_as_skill(d.get('name'), d.get('report'), d.get('mode_name', '')))


@app.route('/api/delete_skill', methods=['POST'])
def api_dsk():
    d = request.json or {}; return _ok(sk.delete_skill(d.get('id')))


@app.route('/api/get_persona_template')
def api_tpl(): return pt.get_template()


@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index_mobile.html')


@app.route('/<path:path>')
def static_f(path):
    return send_from_directory(FRONTEND_DIR, path)


def start_server():
    app.run(host='127.0.0.1', port=8888, debug=False, use_reloader=False)


if __name__ == '__main__':
    # 启动 Flask 线程
    t = threading.Thread(target=start_server, daemon=True)
    t.start()

    # 用 pyjnius 打开 Android WebView
    try:
        import time
        time.sleep(2)

        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity

        WebView = autoclass('android.webkit.WebView')
        WebViewClient = autoclass('android.webkit.WebViewClient')

        webview = WebView(activity)
        settings = webview.getSettings()
        settings.setJavaScriptEnabled(True)
        settings.setDomStorageEnabled(True)
        webview.setWebViewClient(WebViewClient())
        webview.loadUrl('http://127.0.0.1:8888')

        activity.setContentView(webview)

        # 保持线程运行
        import time
        while True:
            time.sleep(1)

    except ImportError:
        # 桌面调试模式
        import webbrowser
        webbrowser.open('http://127.0.0.1:8888')
        print('Server running at http://127.0.0.1:8888')
