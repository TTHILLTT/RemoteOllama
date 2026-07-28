# Buildozer configuration for Android packaging
# Install buildozer: pip install buildozer
# Initial setup: buildozer init
# Build: buildozer android debug

[app]
# App metadata
title = RemoteOllama
package.name = remoteollama
package.domain = com.example
source.dir = app
source.include_exts = py,png,jpg,svg,qml,ttf,txt,json
version = 1.0.0

# Requirements
requirements = python3,hostpython3,pyside6,httpx,markdown,pygments,sqlite3

# Permissions
android.permissions = INTERNET
android.uses_cleartext_traffic = True
android.api = 33
android.minapi = 26
android.ndk = 25b
android.sdk = 33

# Build settings
android.arch = arm64-v8a
android.gradle_dependencies =
android.add_src =

# App settings
orientation = user
fullscreen = 0
window = 1
presplash_color = #1E1E2E
android.presplash_color = #1E1E2E

# Icon & splash (create these files)
# icon.filename = %(source.dir)s/resources/icons/app.png
# presplash.filename = %(source.dir)s/resources/icons/presplash.png

# Qt-specific
p4a.branch = develop
p4a.bootstrap = qt
qt.qml_imports = QtQuick,QtQuick.Controls,QtQuick.Layouts

# Log
log_level = 2
