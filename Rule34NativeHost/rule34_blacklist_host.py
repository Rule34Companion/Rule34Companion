#!/usr/bin/env python3
"""
rule34_blacklist_host.py
Native Messaging host for the Rule34 Tag Filter extension.

Reads/writes a plain-text blacklist file (one image ID per line).
IDs may optionally include a file extension (e.g. "12345.jpg" or "12345") —
both forms are normalised to bare numeric IDs internally, so mixed files work.

The active blacklist path is stored in a small JSON config file alongside
this script, so it survives restarts without needing to re-run install_host.py.
"""

import sys
import json
import struct
import os
import re
import tempfile

# ── Config file (sits next to this script) ────────────────────────────────────

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "r34filter_config.json")

# Default blacklist path — overridden by config file if present
DEFAULT_BLACKLIST_PATH = os.path.expanduser("~/rule34_blacklist.txt")


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def get_blacklist_path():
    cfg = load_config()
    return cfg.get("blacklist_path", DEFAULT_BLACKLIST_PATH)


def set_blacklist_path(new_path):
    new_path = os.path.expanduser(new_path.strip())
    cfg = load_config()
    cfg["blacklist_path"] = new_path
    save_config(cfg)
    return new_path


# ── ID normalisation ──────────────────────────────────────────────────────────

def strip_extension(raw):
    """
    Remove a trailing file extension from an ID string if present.
    '12345.jpg' -> '12345',  '12345' -> '12345',  'abc.png' -> 'abc'
    """
    return re.sub(r'\.[a-zA-Z0-9]{1,5}$', '', raw.strip())


# ── Logging ───────────────────────────────────────────────────────────────────

def log(msg):
    print(f"[r34-host] {msg}", file=sys.stderr, flush=True)


# ── File I/O ──────────────────────────────────────────────────────────────────

def load_ids():
    """
    Return a deduplicated list of bare IDs from the blacklist file.
    Entries like '12345.jpg' are normalised to '12345' on the way in,
    so a file written by an external program with extensions works fine.
    """
    path = get_blacklist_path()
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        raw_lines = [line.strip() for line in f if line.strip()]

    seen = set()
    result = []
    for raw in raw_lines:
        normalised = strip_extension(raw)
        if normalised and normalised not in seen:
            seen.add(normalised)
            result.append(normalised)
    return result


def save_ids(ids):
    """Atomically write the (bare) ID list to the blacklist file."""
    path = get_blacklist_path()
    dir_ = os.path.dirname(os.path.abspath(path))
    os.makedirs(dir_, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dir_, prefix=".r34bl_tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for i in ids:
                f.write(i + "\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ── Native Messaging wire protocol ───────────────────────────────────────────

def read_message():
    raw_len = sys.stdin.buffer.read(4)
    if len(raw_len) < 4:
        return None
    length = struct.unpack("<I", raw_len)[0]
    data = sys.stdin.buffer.read(length)
    return json.loads(data.decode("utf-8"))


def send_message(obj):
    data = json.dumps(obj).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(data)))
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


# ── Request handling ──────────────────────────────────────────────────────────

def handle(msg):
    action = msg.get("action")

    if action == "load":
        ids = load_ids()
        return {"ids": ids, "path": get_blacklist_path()}

    elif action == "add":
        new_id = strip_extension(str(msg.get("id", "")))
        if not new_id:
            return {"error": "no id provided", "ids": load_ids(), "path": get_blacklist_path()}
        ids = load_ids()
        if new_id not in ids:
            ids.append(new_id)
            save_ids(ids)
        return {"ids": ids, "path": get_blacklist_path()}

    elif action == "remove":
        rem_id = strip_extension(str(msg.get("id", "")))
        ids = load_ids()
        ids = [i for i in ids if i != rem_id]
        save_ids(ids)
        return {"ids": ids, "path": get_blacklist_path()}

    elif action == "get_path":
        return {"path": get_blacklist_path()}

    elif action == "set_path":
        raw = str(msg.get("path", "")).strip()
        if not raw:
            return {"error": "no path provided", "path": get_blacklist_path()}
        try:
            new_path = set_blacklist_path(raw)
            # Ensure the new file exists
            if not os.path.exists(new_path):
                os.makedirs(os.path.dirname(os.path.abspath(new_path)), exist_ok=True)
                open(new_path, "a").close()
            ids = load_ids()
            return {"ok": True, "path": new_path, "ids": ids}
        except Exception as e:
            return {"error": str(e), "path": get_blacklist_path()}

    else:
        return {"error": f"unknown action: {action}", "ids": load_ids(), "path": get_blacklist_path()}


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    log(f"started, blacklist path: {get_blacklist_path()}")
    while True:
        msg = read_message()
        if msg is None:
            log("stdin closed, exiting")
            break
        log(f"received: {msg}")
        try:
            response = handle(msg)
        except Exception as e:
            log(f"error handling message: {e}")
            response = {"error": str(e), "ids": []}
        log(f"sending: {response}")
        send_message(response)


if __name__ == "__main__":
    main()
