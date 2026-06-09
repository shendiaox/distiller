[app]
title = Distiller
package.name = distiller
package.domain = org.distiller
source.dir = .
source.include_exts = py,png,jpg,html,css,js,ico
source.include_patterns = frontend/**,backend/**
version = 1.0
requirements = python3,kivy,flask,requests,beautifulsoup4,lxml,python-docx,PyPDF2,openai,pycryptodome,sqlite3
orientation = portrait
fullscreen = 1
android.permissions = INTERNET
android.arch = arm64-v8a
p4a.branch = master
android.allow_download_ccache = 1

[buildozer]
log_level = 2
warn_on_root = 1
