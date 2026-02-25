"""Webhook notification sender. Reads config from state.json, sends to configured targets."""

import io
import json
import sys
import time
import base64
import hmac
import hashlib
from pathlib import Path

# Ensure UTF-8 stdio on all platforms (Windows defaults to GBK/cp936)
for _stream in ('stdin', 'stdout', 'stderr'):
    _cur = getattr(sys, _stream)
    if hasattr(_cur, 'buffer') and _cur.encoding and _cur.encoding.lower().replace('-', '') != 'utf8':
        setattr(sys, _stream, io.TextIOWrapper(_cur.buffer, encoding='utf-8'))

import requests


# --- Feishu ---

def gen_feishu_sign(secret: str, timestamp: str) -> str:
    key = f"{timestamp}\n{secret}".encode("utf-8")
    digest = hmac.new(key, b"", digestmod=hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def send_feishu(url: str, message: str, secret: str | None = None, timeout: int = 10) -> dict:
    payload: dict = {
        "msg_type": "text",
        "content": {"text": message},
    }
    if secret:
        timestamp = str(int(time.time()))
        payload["timestamp"] = timestamp
        payload["sign"] = gen_feishu_sign(secret, timestamp)

    resp = requests.post(url, json=payload, timeout=timeout)
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}

    if resp.status_code != 200:
        return {"status": "error", "error": f"HTTP {resp.status_code}: {data}"}

    if data.get("code", 0) != 0:
        return {"status": "error", "error": f"Feishu error: {data.get('msg', str(data))}"}

    return {"status": "ok"}


# --- Discord ---

def send_discord(url: str, message: str, secret: str | None = None, timeout: int = 10) -> dict:
    payload = {"content": message[:2000]}
    resp = requests.post(url, json=payload, timeout=timeout)

    if resp.status_code == 204:
        return {"status": "ok"}

    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}

    return {"status": "error", "error": f"HTTP {resp.status_code}: {data}"}


# --- WeCom (企业微信) ---

def send_wecom(url: str, message: str, secret: str | None = None, timeout: int = 10) -> dict:
    payload = {"msgtype": "text", "text": {"content": message[:2048]}}
    resp = requests.post(url, json=payload, timeout=timeout)

    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}

    if resp.status_code != 200:
        return {"status": "error", "error": f"HTTP {resp.status_code}: {data}"}

    if data.get("errcode", -1) != 0:
        return {"status": "error", "error": f"WeCom error: {data.get('errmsg', str(data))}"}

    return {"status": "ok"}


# --- Dispatcher ---

SENDERS = {
    "feishu": send_feishu,
    "discord": send_discord,
    "wecom": send_wecom,
}


def notify(watch: str, message: str) -> dict:
    state_path = Path("watches") / watch / "state.json"

    if not state_path.exists():
        return {"success": False, "results": [], "error": f"state.json not found: {state_path}"}

    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    webhooks = state.get("webhooks")
    if not webhooks:
        return {"success": True, "results": [], "error": ""}

    if not webhooks.get("enabled", False):
        return {"success": True, "results": [], "error": ""}

    targets = webhooks.get("targets", [])
    if not targets:
        return {"success": True, "results": [], "error": ""}

    results = []
    for target in targets:
        if not target.get("enabled", True):
            continue

        platform = target.get("platform", "")
        url = target.get("url", "")
        secret = target.get("secret")

        if not url:
            results.append({"url": url, "status": "error", "error": "missing url"})
            continue

        sender = SENDERS.get(platform)
        if not sender:
            results.append({"url": url, "status": "error", "error": f"platform '{platform}' not yet supported"})
            continue

        try:
            result = sender(url=url, message=message, secret=secret)
            result["url"] = url
            results.append(result)
        except Exception as e:
            results.append({"url": url, "status": "error", "error": str(e)})

    has_error = any(r.get("status") == "error" for r in results)
    return {"success": not has_error, "results": results, "error": ""}


if __name__ == "__main__":
    try:
        input_data = json.load(sys.stdin)
        watch = input_data.get("watch", "")
        message = input_data.get("message", "")

        if not watch:
            print(json.dumps({"success": False, "results": [], "error": "missing 'watch' field"}, ensure_ascii=False))
            sys.exit(1)

        if not message:
            print(json.dumps({"success": False, "results": [], "error": "missing 'message' field"}, ensure_ascii=False))
            sys.exit(1)

        result = notify(watch, message)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "results": [], "error": str(e)}, ensure_ascii=False))
        sys.exit(1)
