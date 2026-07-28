# Buildozer configuration for Android packaging (CI-ready)
# Local build: buildozer android debug
# CI build: automated via GitHub Actions

[app]
# App metadata
title = RemoteOllama
package.name = remoteollama
package.domain = com.github.tthilltt
source.dir = app
source.include_exts = py,qml,ttf,txt,json
version = 1.0.0

# Python requirements (recipes from python-for-android)
# sqlite3 is built-in, no need to list
requirements = python3,hostpython3,httpx,markdown

# Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.uses_cleartext_traffic = True
android.api = 33
android.minapi = 26
android.ndk = 25b
android.sdk = 33

# CI: Automatically accept SDK license
android.accept_sdk_license = True

# Build settings
android.arch = arm64-v8a
android.gradle_dependencies =

# App settings
orientation = user
fullscreen = 0
window = 1
presplash_color = #1E1E2E
android.presplash_color = #1E1E2E

# Qt bootstrap (not regular sdl2)
p4a.branch = develop
p4a.bootstrap = qt
qt.qml_imports = QtQuick,QtQuick.Controls,QtQuick.Layouts

# Log
log_level = 2
