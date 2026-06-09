"""
Distiller Android 入口 — Kivy + Flask + WebView
Buildozer 打包时将此文件作为 main.py
"""

import os
import sys
import threading

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# ===== 1. 启动 Flask 后端 =====
from flask import Flask, request, jsonify, send_from_directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')

sys.path.insert(0, BASE_DIR)
from backend.database import init_db
init_db()

import backend.config
import backend.llm_client
import backend.knowledge_base
import backend.distillation
import backend.web_search
import backend.skill_manager
import backend.persona_template

# ---- API 路由（与 mobile_main.py 相同）----
import backend.knowledge_base as kb
import backend.llm_client as llm
import backend.distillation as dist
import backend.web_search as ws
import backend.skill_manager as sk
import backend.persona_template as pt


def _ok(r): return jsonify(r if r is not None else {'ok': False, 'error': '无返回'})


app.add_url_rule('/api/hello', 'hello', lambda: jsonify('Distiller Mobile OK'))
app.add_url_rule('/api/get_config', 'cfg', lambda: jsonify(backend.config.load_config()))
app.add_url_rule('/api/set_api_key', 'set_key', lambda: _ok(backend.config.set_api_key((request.json or {}).get('key', ''))), methods=['POST'])
app.add_url_rule('/api/test_api_connection', 'test_conn', lambda: _ok(llm.test_api_connection()))


@app.route('/api/send_message', methods=['POST'])
def api_chat():
    d = request.json or {}
    return _ok(llm.send_message(d.get('message', ''), d.get('history', []), d.get('kb_id'), d.get('skill_id')))


@app.route('/api/list_knowledge_bases')
def api_list_kb(): return jsonify(kb.list_knowledge_bases())
@app.route('/api/create_knowledge_base', methods=['POST'])
def api_create_kb():
    d = request.json or {}; return _ok(kb.create_knowledge_base(d.get('name', ''), d.get('description', '')))
@app.route('/api/rename_knowledge_base', methods=['POST'])
def api_rename_kb():
    d = request.json or {}; return _ok(kb.rename_knowledge_base(d.get('kb_id'), d.get('name', '')))
@app.route('/api/delete_knowledge_base', methods=['POST'])
def api_delete_kb():
    d = request.json or {}; return _ok(kb.delete_knowledge_base(d.get('kb_id')))
@app.route('/api/ingest_text', methods=['POST'])
def api_ingest():
    d = request.json or {}; return _ok(kb.ingest_text(d.get('kb_id'), d.get('title', ''), d.get('text', '')))
@app.route('/api/ingest_file', methods=['POST'])
def api_ingest_file():
    d = request.json or {}; return _ok(kb.ingest_file(d.get('kb_id'), d.get('filepath', ''), d.get('title')))
@app.route('/api/search_knowledge_base')
def api_search():
    return jsonify(kb.search_knowledge_base(request.args.get('kb_id', 1), request.args.get('query', ''), int(request.args.get('k', 5))))
@app.route('/api/get_kb_documents')
def api_docs():
    return jsonify(kb.get_kb_documents(request.args.get('kb_id', 1)))
@app.route('/api/get_kb_stats')
def api_stats():
    return jsonify(kb.get_kb_stats(request.args.get('kb_id', 1)))
@app.route('/api/delete_document', methods=['POST'])
def api_del_doc():
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
def api_search_web():
    return jsonify(ws.web_search(request.args.get('query', ''), int(request.args.get('max', 10))))
@app.route('/api/fetch_and_ingest_urls', methods=['POST'])
def api_fetch():
    d = request.json or {}; return _ok(ws.fetch_and_ingest_urls(d.get('kb_id'), d.get('urls', [])))
@app.route('/api/list_skills')
def api_list_sk(): return jsonify(sk.list_skills())
@app.route('/api/create_skill', methods=['POST'])
def api_create_sk():
    d = request.json or {}; return _ok(sk.create_skill(d.get('name'), d.get('type'), d.get('system_prompt'), d.get('description', '')))
@app.route('/api/update_skill', methods=['POST'])
def api_update_sk():
    d = request.json or {}; return _ok(sk.update_skill(d.get('id'), d.get('name'), d.get('system_prompt'), d.get('description', '')))
@app.route('/api/delete_skill', methods=['POST'])
def api_del_sk():
    d = request.json or {}; return _ok(sk.delete_skill(d.get('id')))
@app.route('/api/get_skill')
def api_get_sk(): return jsonify(sk.get_skill(int(request.args.get('id', 0))))
@app.route('/api/save_distill_as_skill', methods=['POST'])
def api_save_sk():
    d = request.json or {}; return _ok(sk.save_distill_as_skill(d.get('name'), d.get('report'), d.get('mode_name', '')))
@app.route('/api/get_persona_template')
def api_tpl(): return pt.get_template()


@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index_mobile.html')


@app.route('/<path:path>')
def static_f(path):
    return send_from_directory(FRONTEND_DIR, path)


def start_flask():
    app.run(host='127.0.0.1', port=8888, debug=False, use_reloader=False)


# ===== 2. Kivy WebView 壳 =====
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.clock import Clock

# 尝试加载 Android WebView
try:
    from android.webkit import WebView as AndroidWebView
    HAS_ANDROID = True
except ImportError:
    HAS_ANDROID = False

if HAS_ANDROID:
    # Android 原生 WebView（性能更好）
    from jnius import autoclass, cast
    WebView = autoclass('android.webkit.WebView')
    WebViewClient = autoclass('android.webkit.WebViewClient')
    WebSettings = autoclass('android.webkit.WebSettings')
    LayoutParams = autoclass('android.view.ViewGroup$LayoutParams')
    LinearLayout = autoclass('android.widget.LinearLayout')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
else:
    # 桌面调试用
    import webbrowser


class DistillerApp(App):
    def build(self):
        # 启动 Flask 线程
        t = threading.Thread(target=start_flask, daemon=True)
        t.start()

        if HAS_ANDROID:
            # 用原生 WebView
            Clock.schedule_once(self._setup_webview, 2)
            return BoxLayout()
        else:
            # 桌面：打开浏览器
            import webbrowser
            import time
            time.sleep(1.5)
            webbrowser.open('http://127.0.0.1:8888')
            from kivy.uix.label import Label
            return Label(text='Distiller 已启动\n请在浏览器打开 http://127.0.0.1:8888')

    def _setup_webview(self, dt):
        activity = PythonActivity.mActivity
        webview = WebView(activity)
        settings = webview.getSettings()
        settings.setJavaScriptEnabled(True)
        settings.setDomStorageEnabled(True)
        settings.setAllowFileAccess(True)
        webview.setWebViewClient(WebViewClient())
        webview.loadUrl('http://127.0.0.1:8888')
        activity.setContentView(webview)


if __name__ == '__main__':
    DistillerApp().run()
