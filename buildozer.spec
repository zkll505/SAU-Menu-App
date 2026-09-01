[app]
title = Southern Menu
package.name = southernmenu
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

requirements = python3,kivy,requests,beautifulsoup4,certifi,chardet,idna,urllib3,soupsieve

orientation = portrait
fullscreen = 0

# Needed for HTTPS requests on Android
android.permissions = INTERNET

android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.build_tools = 33.0.2
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
