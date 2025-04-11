"""
Copyright (C) 2025 Fern Lane, simple-status-server

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
See the License for the specific language governing permissions and
limitations under the License.

IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""

import os
import platform

import PyInstaller.config

# from PyInstaller.utils.hooks import collect_data_files

# Set working path
PyInstaller.config.CONF["workpath"] = "./build"

# Parse version from _version.py file
with open(os.path.join("simple_status_server", "_version.py"), "r", encoding="utf-8") as file:
    version = file.read().strip().split("__version__")[-1].split('"')[1]

# Final name
COMPILE_NAME = f"simple-status-server-{version}-{platform.system()}-{platform.machine()}".lower()

SOURCE_FILES = [os.path.join("simple_status_server", "__main__.py")]
INCLUDE_FILES = [
    ("LICENSE", "."),
    (os.path.join("simple_status_server", "static"), os.path.join("simple_status_server", "static")),
    (os.path.join("simple_status_server", "templates"), os.path.join("simple_status_server", "templates")),
]
ICON = None  # [os.path.join("icons", "icon.ico")]

# Fix SSL: CERTIFICATE_VERIFY_FAILED
# INCLUDE_FILES.extend(collect_data_files("certifi"))
HIDDEN_IMPORTS = []  # = ["certifi"]

a = Analysis(
    SOURCE_FILES,
    pathex=[],
    binaries=[],
    datas=INCLUDE_FILES,
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["_bootlocale", "__pycache__"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    exclude_binaries=False,
    name=COMPILE_NAME,
    debug=False,
    bootloader_ignore_signals=True,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON,
)
