"""应用配置管理 — JSON 配置文件 + @eel.expose 接口"""

import json
import os
import eel

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
CONFIG_PATH = os.path.join(DATA_DIR, 'config.json')

DEFAULTS = {
    'deepseek_api_key': '',
    'deepseek_model': 'deepseek-chat',
    'deepseek_base_url': 'https://api.deepseek.com',
    'http_timeout': 30,
    'embedding_model': 'all-MiniLM-L6-v2',
    'retrieval_k': 5,
}


def load_config():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULTS)
        return DEFAULTS.copy()
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    for k, v in DEFAULTS.items():
        cfg.setdefault(k, v)
    return cfg


def save_config(cfg):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


@eel.expose
def get_config():
    cfg = load_config()
    api_key = cfg.get('deepseek_api_key', '')
    cfg['deepseek_api_key'] = _mask_key(api_key)
    return cfg


@eel.expose
def set_api_key(key):
    cfg = load_config()
    cfg['deepseek_api_key'] = key.strip()
    save_config(cfg)
    return {'ok': True}


@eel.expose
def set_setting(key, value):
    cfg = load_config()
    if key in cfg:
        cfg[key] = value
        save_config(cfg)
        return {'ok': True}
    return {'ok': False, 'error': f'未知设置项: {key}'}


def get_api_key():
    return load_config().get('deepseek_api_key', '')


def get_setting(key):
    return load_config().get(key, DEFAULTS.get(key))


def _mask_key(key):
    if len(key) <= 8:
        return '*' * len(key)
    return key[:4] + '*' * (len(key) - 8) + key[-4:]
