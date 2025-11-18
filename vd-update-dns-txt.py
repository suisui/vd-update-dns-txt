#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Value-Domain VDAPI を使って TXT レコードを更新するスクリプト（設定ファイル / dry-run 対応）
"""

import argparse
import configparser
import sys
from typing import List, Dict, Any, Tuple, Optional

import requests

API_BASE = "https://api.value-domain.com/v1"


# ---------------------------
# 設定ファイルから API キーを読み込む
# ---------------------------

def load_api_key(config_path: str) -> str:
    config = configparser.ConfigParser()
    read_files = config.read(config_path, encoding="utf-8")

    if not read_files:
        print(f"ERROR: 設定ファイル '{config_path}' が読み込めません。", file=sys.stderr)
        sys.exit(1)

    if "valuedomain" not in config or "api_key" not in config["valuedomain"]:
        print(f"ERROR: [{config_path}] に [valuedomain]/api_key がありません。", file=sys.stderr)
        sys.exit(1)

    api_key = config["valuedomain"]["api_key"].strip()
    if not api_key:
        print(f"ERROR: 設定ファイル '{config_path}' の api_key が空です。", file=sys.stderr)
        sys.exit(1)

    return api_key


# ---------------------------
# DNS レコードのパース／整形
# ---------------------------

def parse_records(records_str: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for line in records_str.splitlines():
        line = line.rstrip()
        if not line:
            continue

        parts = line.split(None, 3)
        if len(parts) == 2:
            rtype, target = parts
            content = ""
        elif len(parts) >= 3:
            rtype, target = parts[0], parts[1]
            content = " ".join(parts[2:])
        else:
            records.append({"raw": line})
            continue

        records.append({"type": rtype.lower(), "target": target, "content": content})

    return records


def build_records_string(records: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for r in records:
        if "raw" in r:
            lines.append(r["raw"])
            continue

        rtype = r.get("type", "")
        target = r.get("target", "")
        content = r.get("content", "")

        if content:
            lines.append(f"{rtype} {target} {content}")
        else:
            lines.append(f"{rtype} {target}")

    return "\n".join(lines)


# ---------------------------
# fullname → target 変換
# ---------------------------

def fullname_to_target(fullname: str, domain: str) -> str:
    fullname = fullname.rstrip(".")
    domain = domain.rstrip(".")

    if fullname in ("@", "*"):
        return fullname

    if fullname == domain:
        return "@"

    suffix = "." + domain
    if fullname.endswith(suffix):
        host = fullname[: -len(suffix)].rstrip(".")
        if host == "*":
            return "*"
        return host or "@"

    return fullname


# ---------------------------
# Value-Domain API 呼び出し
# ---------------------------

def get_dns(api_key: str, domain: str) -> Tuple[str, str, Optional[int]]:
    url = f"{API_BASE}/domains/{domain}/dns"
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}

    resp = requests.get(url, headers=headers, timeout=20)
    if resp.status_code != 200:
        print(f"ERROR: GET DNS failed ({resp.status_code})", file=sys.stderr)
        print(resp.text, file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    results = data.get("results", {})
    ns_type = results.get("ns_type")
    records_str = results.get("records", "") or ""
    ttl = results.get("ttl")

    try:
        ttl_int = int(ttl) if ttl is not None else None
    except (ValueError, TypeError):
        ttl_int = None

    if not ns_type:
        print("ERROR: ns_type がありません。Value-Domain の NS を確認してください。", file=sys.stderr)
        sys.exit(1)

    return ns_type, records_str, ttl_int


def put_dns(api_key: str, domain: str, ns_type: str, records_str: str, ttl: Optional[int]) -> None:
    url = f"{API_BASE}/domains/{domain}/dns"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload: Dict[str, Any] = {"ns_type": ns_type, "records": records_str}
    if ttl is not None:
        payload["ttl"] = ttl

    resp = requests.put(url, headers=headers, json=payload, timeout=20)
    if resp.status_code != 200:
        print(f"ERROR: PUT DNS failed ({resp.status_code})", file=sys.stderr)
        print(resp.text, file=sys.stderr)
        sys.exit(1)

    print("DNS updated successfully.")
    try:
        print("Response:", resp.json())
    except Exception:
        pass


# ---------------------------
# TXT レコード更新ロジック
# ---------------------------

def update_txt_record(api_key: str, domain: str, record_name: str, token: str, dry_run: bool) -> None:
    print(f"[INFO] Domain: {domain}")
    print(f"[INFO] Record: {record_name}")
    print(f"[INFO] Token:  {token}")

    # 1) GET で現在の DNS を読む
    ns_type, records_str, ttl = get_dns(api_key, domain)

    print(f"[INFO] ns_type: {ns_type}, ttl: {ttl}")

    records = parse_records(records_str)
    target = fullname_to_target(record_name, domain)
    print(f"[INFO] target → {target}")

    new_records: List[Dict[str, Any]] = []
    replaced = False

    for r in records:
        if "raw" in r:
            new_records.append(r)
            continue

        if r["type"] == "txt" and r["target"] == target:
            if not replaced:
                new_records.append({"type": "txt", "target": target, "content": token})
                replaced = True
            else:
                print(f"[INFO] Remove duplicate TXT: {r}")
        else:
            new_records.append(r)

    if not replaced:
        new_records.append({"type": "txt", "target": target, "content": token})
        print(f"[INFO] Add new TXT record.")

    new_records_str = build_records_string(new_records)

    # ---------------------------
    # DRY-RUN モード
    # ---------------------------
    if dry_run:
        print("\n===== DRY RUN: 以下の内容で PUT されます =====")
        print(f"ns_type: {ns_type}")
        print(f"ttl:     {ttl}")
        print("records:")
        print(new_records_str)
        print("===== DRY RUN END =====")
        return

    # ---------------------------
    # 実際に PUT する
    # ---------------------------
    put_dns(api_key, domain, ns_type, new_records_str, ttl)


# ---------------------------
# CLI
# ---------------------------

def main():
    parser = argparse.ArgumentParser(description="Value-Domain TXT updater (with dry-run)")
    parser.add_argument("--config", default="app-config.ini", help="INI 設定ファイル")
    parser.add_argument("--domain", required=True)
    parser.add_argument("--record-name", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--dry-run", action="store_true", help="PUT を実行せず変更内容を表示して終了")

    args = parser.parse_args()

    api_key = load_api_key(args.config)

    update_txt_record(
        api_key=api_key,
        domain=args.domain,
        record_name=args.record_name,
        token=args.token,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
