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
# openssl: required for HTTPS/SSL in requests
# requests: HTTP client (replaces httpx for p4a compatibility)
# markdown: pure-Python (uses pip fallback if no recipe)
requirements = python3,hostpython3,openssl,requests,markdown

# Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.uses_cleartext_traffic = True
android.api = 33
android.minapi = 26
android.ndk = 25c
android.sdk = 33

# CI: Automatically accept SDK license
android.accept_sdk_license = True

# Build settings
android.arch = arm64-v8a

# App display
orientation = all
fullscreen = 0
presplash_color = #1E1E2E
android.presplash_color = #1E1E2E

# Qt bootstrap (provides PySide6/QML on Android via prebuilt Qt libraries)
# Pin p4a to v2026.05.09 (last known-good version before --qt-libs regression)
p4a.url = https://github.com/kivy/python-for-android
p4a.commit = v2026.05.09
p4a.bootstrap = qt
qt.qml_imports = QtQuick,QtQuick.Controls,QtQuick.Layouts

# Allow pip fallback for pure-Python packages without p4a recipes
p4a.ignore_setup_py = False

# Log
log_level = 2
