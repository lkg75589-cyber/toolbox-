[app]
title = Toolbox 30
package.name = toolbox30
package.domain = org.toolbox
source.dir = .
source.include_exts = py
version = 1.0
requirements = python3,flask,werkzeug,jinja2,markupsafe,itsdangerous,click,blinker,pypdf
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True
p4a.bootstrap = webview
p4a.port = 5000

[buildozer]
log_level = 2
warn_on_root = 1
