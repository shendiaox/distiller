[app]
title = Distiller
package.name = distiller
package.domain = org.distiller
source.dir = .
source.include_exts = py,png,jpg,html,css,js,ico
source.include_patterns = frontend/**,backend/**
version = 1.0
requirements = python3,kivy,flask,requests,beautifulsoup4,lxml,python-docx,PyPDF2,openai,pycryptodome
orientation = portrait
fullscreen = 1
android.permissions = INTERNET
android.api = 33
android.minapi = 26
android.ndk = 25b
android.sdk = 33
android.arch = arm64-v8a
p4a.branch = develop
p4a.hook =

[buildozer]
log_level = 2
warn_on_root = 1
