# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('frontend', 'frontend'),
    ],
    hiddenimports=[
        'eel', 'bottle', 'gevent', 'geventwebsocket',
        'sqlite3',
        'chromadb', 'chromadb.db', 'chromadb.utils',
        'sentence_transformers', 'sentence_transformers.models',
        'transformers', 'transformers.models',
        'torch', 'numpy',
        'openai',
        'duckduckgo_search',
        'bs4', 'lxml',
        'docx',
        'PyPDF2',
        'requests',
        'skops', 'skops.io',
        'huggingface_hub',
        'onnxruntime',
        'tiktoken', 'tiktoken_ext',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Distiller',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Distiller',
)
