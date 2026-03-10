#!/usr/bin/env python3
"""
install_host.py
Installs (or uninstalls) the Rule34 Blacklist native messaging host for Firefox.

Usage:
    python install_host.py                                    # Install (default blacklist path)
    python install_host.py --blacklist /path/to/list.txt     # Install with custom blacklist path
    python install_host.py --remove                          # Uninstall
    python install_host.py --status                          # Show current status

Supported platforms: Linux, macOS, Windows
"""

import sys
import os
import json
import stat
import argparse
import platform

# ── Config ────────────────────────────────────────────────────────────────────

HOST_NAME   = "rule34_blacklist_host"
HOST_SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "rule34_blacklist_host.py"))
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "r34filter_config.json")

# Extension UUID — update this after you install the extension in Firefox
# Go to about:debugging -> This Firefox -> find "Rule34 Unlimited Tag Filter" -> copy the ID
EXTENSION_ID = "You_ID_Here@temporary-addon"

DEFAULT_BLACKLIST_PATH = os.path.expanduser("~/rule34_blacklist.txt")

# ── Platform detection ────────────────────────────────────────────────────────

def get_manifest_dir():
    system = platform.system()
    if system == "Linux":
        return os.path.expanduser("~/.mozilla/native-messaging-hosts")
    elif system == "Darwin":
        return os.path.expanduser("~/Library/Application Support/Mozilla/NativeMessagingHosts")
    elif system == "Windows":
        return os.path.join(os.environ.get("APPDATA", ""), "Mozilla", "NativeMessagingHosts")
    else:
        print(f"WARNING: Unknown platform '{system}'. Defaulting to Linux path.")
        return os.path.expanduser("~/.mozilla/native-messaging-hosts")


def get_manifest_path(manifest_dir):
    return os.path.join(manifest_dir, f"{HOST_NAME}.json")


def get_python_path():
    return sys.executable


# ── Config file helpers ───────────────────────────────────────────────────────

def write_config(blacklist_path):
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                cfg = json.load(f)
        except Exception:
            pass
    cfg["blacklist_path"] = os.path.abspath(os.path.expanduser(blacklist_path))
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    print(f"  Config written : {CONFIG_PATH}")


def read_config_path():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                return json.load(f).get("blacklist_path", DEFAULT_BLACKLIST_PATH)
        except Exception:
            pass
    return DEFAULT_BLACKLIST_PATH


# ── Native Messaging manifest ─────────────────────────────────────────────────

def build_manifest():
    system = platform.system()
    if system == "Windows":
        wrapper = os.path.join(os.path.dirname(HOST_SCRIPT), f"{HOST_NAME}.bat")
        path = wrapper
    else:
        path = HOST_SCRIPT

    return {
        "name": HOST_NAME,
        "description": "Rule34 image-ID blacklist host",
        "path": path,
        "type": "stdio",
        "allowed_extensions": [EXTENSION_ID]
    }


# ── Windows helpers ───────────────────────────────────────────────────────────

def set_windows_registry(manifest_path, remove=False):
    try:
        import winreg
    except ImportError:
        print("  (winreg not available — skipping registry step)")
        return

    reg_key = r"SOFTWARE\Mozilla\NativeMessagingHosts\\" + HOST_NAME
    try:
        if remove:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, reg_key)
            print("  Registry key removed.")
        else:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_key)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, manifest_path)
            winreg.CloseKey(key)
            print(f"  Registry key set: HKCU\\{reg_key}")
    except Exception as e:
        print(f"  WARNING: Registry operation failed: {e}")


def create_windows_wrapper():
    wrapper = os.path.join(os.path.dirname(HOST_SCRIPT), f"{HOST_NAME}.bat")
    py = get_python_path()
    with open(wrapper, "w") as f:
        f.write(f'@echo off\n"{py}" "{HOST_SCRIPT}" %*\n')
    print(f"  Created wrapper : {wrapper}")
    return wrapper


# ── Shebang patcher ───────────────────────────────────────────────────────────

def patch_shebang(script_path, python_path):
    with open(script_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if lines and lines[0].startswith("#!"):
        lines[0] = f"#!{python_path}\n"
        with open(script_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"  Updated shebang : {lines[0].strip()}")


# ── Install ───────────────────────────────────────────────────────────────────

def install(blacklist_path):
    system        = platform.system()
    manifest_dir  = get_manifest_dir()
    manifest_path = get_manifest_path(manifest_dir)
    blacklist_path = os.path.abspath(os.path.expanduser(blacklist_path))

    print("=== Rule34 Blacklist Host Installer ===\n")
    print(f"Platform        : {system}")
    print(f"Python          : {get_python_path()}")
    print(f"Host script     : {HOST_SCRIPT}")
    print(f"Manifest dir    : {manifest_dir}")
    print(f"Manifest path   : {manifest_path}")
    print(f"Blacklist file  : {blacklist_path}")
    print()

    # 1. Make the script executable
    if system != "Windows":
        os.chmod(HOST_SCRIPT, os.stat(HOST_SCRIPT).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"  Made executable: {HOST_SCRIPT}")
        patch_shebang(HOST_SCRIPT, get_python_path())

    # 2. Create manifest directory
    os.makedirs(manifest_dir, exist_ok=True)
    print(f"  Created dir    : {manifest_dir}")

    # 3. Windows: .bat wrapper
    if system == "Windows":
        create_windows_wrapper()

    # 4. Write the JSON manifest
    manifest = build_manifest()
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"  Wrote manifest : {manifest_path}")

    # 5. Windows: registry key
    if system == "Windows":
        set_windows_registry(manifest_path)

    # 6. Write config (stores blacklist path for the host script)
    write_config(blacklist_path)

    # 7. Ensure blacklist file exists
    if not os.path.exists(blacklist_path):
        os.makedirs(os.path.dirname(blacklist_path), exist_ok=True)
        open(blacklist_path, "a").close()
        print(f"  Created blacklist file: {blacklist_path}")
    else:
        print(f"  Blacklist file already exists: {blacklist_path}")

    print()
    print("✅ Installation complete!")
    print()
    print("Next steps:")
    print("  1. Open Firefox -> about:debugging -> This Firefox")
    print("  2. Load the extension (Load Temporary Add-on) or install permanently")
    print("  3. Copy the Extension ID shown there")
    print("  4. Edit install_host.py and set EXTENSION_ID = '<your-id>'")
    print("  5. Run this script again")
    print()
    print(f"  Blacklist file : {blacklist_path}")
    print(f"  Config file    : {CONFIG_PATH}")
    print()
    print("  To change the blacklist path later, use the path field in the")
    print("  extension popup — no need to re-run this script.")


# ── Uninstall ─────────────────────────────────────────────────────────────────

def uninstall():
    system        = platform.system()
    manifest_dir  = get_manifest_dir()
    manifest_path = get_manifest_path(manifest_dir)

    print("=== Uninstalling Rule34 Blacklist Host ===\n")

    if os.path.exists(manifest_path):
        os.remove(manifest_path)
        print(f"  Removed: {manifest_path}")
    else:
        print(f"  Not found (already removed?): {manifest_path}")

    if system == "Windows":
        set_windows_registry(manifest_path, remove=True)
        wrapper = os.path.join(os.path.dirname(HOST_SCRIPT), f"{HOST_NAME}.bat")
        if os.path.exists(wrapper):
            os.remove(wrapper)
            print(f"  Removed wrapper: {wrapper}")

    bl = read_config_path()
    print()
    print("✅ Uninstalled. The following files were NOT deleted:")
    print(f"   Blacklist : {bl}")
    print(f"   Config    : {CONFIG_PATH}")


# ── Status ────────────────────────────────────────────────────────────────────

def status():
    manifest_dir  = get_manifest_dir()
    manifest_path = get_manifest_path(manifest_dir)
    bl_path       = read_config_path()

    print("=== Rule34 Blacklist Host Status ===\n")
    print(f"Platform       : {platform.system()}")
    print(f"Host script    : {HOST_SCRIPT}  {'[EXISTS]' if os.path.exists(HOST_SCRIPT) else '[MISSING]'}")
    print(f"Config file    : {CONFIG_PATH}  {'[EXISTS]' if os.path.exists(CONFIG_PATH) else '[MISSING]'}")
    print(f"Manifest       : {manifest_path}  {'[EXISTS]' if os.path.exists(manifest_path) else '[MISSING]'}")
    print(f"Blacklist file : {bl_path}  {'[EXISTS]' if os.path.exists(bl_path) else '[MISSING]'}")

    if os.path.exists(bl_path):
        with open(bl_path) as f:
            ids = [l.strip() for l in f if l.strip()]
        print(f"  -> {len(ids)} line(s) in blacklist")

    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            m = json.load(f)
        print(f"\nManifest contents:")
        print(json.dumps(m, indent=2))


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Install/uninstall the Rule34 blacklist native host")
    parser.add_argument("--blacklist", default=DEFAULT_BLACKLIST_PATH,
                        help=f"Path to the blacklist text file (default: {DEFAULT_BLACKLIST_PATH})")
    parser.add_argument("--remove", action="store_true", help="Uninstall the host")
    parser.add_argument("--status", action="store_true", help="Show installation status")
    args = parser.parse_args()

    if args.remove:
        uninstall()
    elif args.status:
        status()
    else:
        install(args.blacklist)
