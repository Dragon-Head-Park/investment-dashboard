#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
업데이트 로그 헬퍼 (v2 — JSON 기반)

v1: HTML 본문 정규식 치환 → truncation 사고 빈발
v2: data/update_log.json 만 read/write, HTML 본문 절대 미수정
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
JSON_PATH = DATA_DIR / "update_log.json"
JS_PATH = DATA_DIR / "update_log.js"

JS_HEADER = (
    "// auto-generated from data/update_log.json - 직접 편집 금지\n"
    "// HTML <script src> 로 로드되어 window.__updateLog 에 주입됨\n"
)


def _load_log():
    if not JSON_PATH.exists():
        return []
    try:
        with JSON_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        return data
    except json.JSONDecodeError as e:
        bak = JSON_PATH.with_suffix(".json.broken")
        JSON_PATH.replace(bak)
        print("[ERROR] update_log.json 파싱 실패 - %s (%s)" % (bak.name, e))
        return []


def _atomic_write(path, text):
    DATA_DIR.mkdir(exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass
    tmp.replace(path)


def _save_log(log_list):
    json_text = json.dumps(log_list, ensure_ascii=False, indent=2)
    _atomic_write(JSON_PATH, json_text)
    compact = json.dumps(log_list, ensure_ascii=False, separators=(",", ":"))
    _atomic_write(JS_PATH, JS_HEADER + "window.__updateLog = " + compact + ";\n")


def add_update_log(*args, **kwargs):
    """
    엔트리 추가 (v1 호환).
      add_update_log(task_id=..., updates=[...])
      add_update_log(html_path=..., task_id=..., updates=[...])
      add_update_log(html_path, task_id, updates)
    """
    if "task_id" in kwargs and "updates" in kwargs:
        task_id = kwargs["task_id"]
        updates = kwargs["updates"]
        max_entries = kwargs.get("max_entries", 50)
    else:
        if len(args) == 3:
            _, task_id, updates = args
        elif len(args) == 2:
            task_id, updates = args
        else:
            raise TypeError("task_id 와 updates 인자가 필요합니다")
        max_entries = kwargs.get("max_entries", 50)

    if not isinstance(updates, list):
        raise TypeError("updates 는 list 여야 함")
    for u in updates:
        if not isinstance(u, dict):
            raise TypeError("각 update 는 dict 여야 함")
        if "tab" not in u or "label" not in u or "items" not in u:
            raise ValueError("update 에 tab/label/items 필수")

    current = _load_log()
    new_entry = {
        "taskId": task_id,
        "time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "updates": updates,
    }
    current.append(new_entry)
    if len(current) > max_entries:
        current = current[-max_entries:]

    _save_log(current)

    total_items = sum(len(u.get("items", [])) for u in updates)
    print("[OK] update_log 기록 완료")
    print("     task: " + task_id)
    print("     time: " + new_entry["time"])
    print("     섹션: %d개, 항목: %d개" % (len(updates), total_items))
    for u in updates:
        items = u.get("items", [])
        preview = ", ".join(items[:3])
        if len(items) > 3:
            preview += " ... (+%d개)" % (len(items) - 3)
        print("     - %s: %s" % (u.get("label", "?"), preview))
    return True


def log_stock_price_update(html_path, task_id, tab, section_id, section_label, stock_updates):
    items = [n + " " + p + " (" + c + ")" for n, p, c in stock_updates]
    return add_update_log(task_id=task_id, updates=[{
        "tab": tab,
        "sectionId": section_id,
        "label": section_label,
        "items": items,
    }])


def log_multi_section_update(html_path, task_id, sections):
    updates = [{
        "tab": tab, "sectionId": sid, "label": lbl, "items": items
    } for tab, sid, lbl, items in sections]
    return add_update_log(task_id=task_id, updates=updates)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        add_update_log(task_id="test-task", updates=[{
            "tab": "stocks",
            "sectionId": "sub-portfolio",
            "label": "테스트 섹션",
            "items": ["TEST $1.00 (+0.0%)"],
        }])
        print("\n테스트 entry 추가됨.")
        log = _load_log()
        print(json.dumps(log[-1], ensure_ascii=False, indent=2))
