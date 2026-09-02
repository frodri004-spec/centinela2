[app]

# (str) Title of your application
title = Centinela

# (str) Package name
package.name = centinela

# (str) Package domain (needed for android/ios packaging)
package.domain = com.centinela

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty for all)
source.include_exts = py,png,jpg,kv,atlas

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) List of exclusions using pattern matching
#source.exclude_patterns = license,images/*/*.jpg

# (str) Application versioning (method 1)
version = 0.1.0

# (str) Application requirements
requirements = python3,kivy

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash of the app
#presplash.filename = %(source.dir)s/data/presplash.png

# (string) Icon of the app
#icon.filename = %(source.dir)s/data/icon.png

# (list) Permissions
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION

# (int) Target Android API, should be as high as possible.
android.api = 31

# (int) Minimum API your APK will support
android.minapi = 21

# (str) Android logcat filters to use
#android.logcat_filters = *:S python:D

# (bool) Use --private data in the package
#android.private_storage = True

# (str) Android NDK directory (if blank, it will be automatically downloaded.)
#android.ndk_path =

# (str) Android SDK directory (if blank, it will be automatically downloaded.)
#android.sdk_path =

# (str) Android entry point, default is ok for Kivy-based app
#android.entrypoint = org.kivy.android.PythonActivity

# (list) List of Java .jar files to add
#android.add_jars = foo.jar

# (list) List of Java files to add
#android.add_src =

# (list) Android AAR libraries to add
#android.add_aars =

# (str) xml to include in manifest
#android.manifest =

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a

# (int) Use build number for version code
#android.numeric_version = 1

# (str) Python package to install
#p4a.branch = master

# (int) Wait for Android device to connect
#android.skip_adb = False

# (bool) Launch application after build
#android.launch = True

[buildozer]
# (int) Log level (0 = quiet, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning related to the build
warn_on_root = 1

# (str) Path to buildozer
#buildozer = /usr/local/bin/buildozer

# (str) Build directory
build_dir = .buildozer

# (str) Source directory for distro packages
#dist_dir = .buildozer/dist

# (int) Build with Python 3
#python_version = 3
