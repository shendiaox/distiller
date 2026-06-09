"""
Distiller（万物可蒸馏）— 桌面知识蒸馏工具
Entry point: python main.py
"""

import os
# 国内 HuggingFace 镜像，必须在导入 sentence-transformers 之前设置
os.environ['HF_ENDPOINT'] = 'https://www.modelscope.cn'

import eel
import eel.browsers as eel_browsers

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

eel.init(FRONTEND_DIR)

from backend.database import init_db

init_db()

import backend.config          # noqa
import backend.llm_client      # noqa
import backend.knowledge_base  # noqa
import backend.distillation    # noqa
import backend.web_search      # noqa
import backend.skill_manager   # noqa
import backend.persona_template # noqa


@eel.expose
def hello():
    return "Distiller backend is running!"


def _find_browser():
    """找到可用的浏览器（含 WebView2 运行时）"""
    candidates = [
        # Chrome 标准路径
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        os.path.expandvars(r'%LocalAppData%\Google\Chrome\Application\chrome.exe'),
        # Edge 标准路径
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    ]

    # 额外：搜索 Edge WebView2 运行时（Windows 10/11 通常自带）
    import glob
    webview_dirs = glob.glob(r'C:\Program Files (x86)\Microsoft\EdgeCore\*\msedge.exe')
    webview_dirs += glob.glob(r'C:\Program Files\Microsoft\EdgeCore\*\msedge.exe')
    candidates.extend(webview_dirs)

    for p in candidates:
        if os.path.isfile(p):
            import subprocess
            try:
                r = subprocess.run([p, '--version'], capture_output=True, timeout=5)
                if r.returncode == 0:
                    return p
                # EdgeCore 可能没有 --version 但可以启动，直接尝试
                if 'EdgeCore' in p:
                    return p
            except Exception:
                continue
    return None


def _get_local_ip():
    """获取本机局域网 IP"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('114.114.114.114', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def _add_firewall_rule(port):
    """添加 Windows 防火墙入站规则"""
    import subprocess
    try:
        subprocess.run([
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            f'name=Distiller Port {port}',
            'dir=in', 'action=allow', 'protocol=TCP',
            f'localport={port}',
        ], capture_output=True, check=False)
    except Exception:
        pass  # 非管理员权限时静默跳过


if __name__ == '__main__':
    PORT = 8888
    local_ip = _get_local_ip()
    _add_firewall_rule(PORT)

    browser = _find_browser()

    if browser:
        if 'edge' in browser.lower():
            eel_browsers.set_path('edge', browser)
            mode = 'edge'
        else:
            eel_browsers.set_path('chrome', browser)
            mode = 'chrome'
        print(f'浏览器: {browser}')
        print('')
        print(f'  === 手机浏览器打开这个地址 ===')
        print(f'  http://{local_ip}:{PORT}/index.html')
        print(f'  （手机和电脑必须连同一个WiFi）')
        print('')
        eel.start(
            'index.html',
            mode=mode,
            size=(1400, 900),
            port=PORT,
            host='0.0.0.0',
            cmdline_args=['--disable-extensions'],
        )
    else:
        print('')
        print(f'  === 手机浏览器打开这个地址 ===')
        print(f'  http://{local_ip}:{PORT}/index.html')
        print(f'  （手机和电脑必须连同一个WiFi）')
        print('')
        eel.start(
            'index.html',
            mode=None,
            size=(1400, 900),
            port=PORT,
            host='0.0.0.0',
        )
