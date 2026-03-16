#!/usr/bin/env python3
"""
업데이트 로그 헬퍼 — 스케줄 태스크에서 대시보드 HTML의 __updateLog에 기록을 추가합니다.

사용법:
    from update_log_helper import add_update_log

    add_update_log(
        html_path="주식시장_대시보드.html",
        task_id="kr-market-dashboard-update",
        updates=[
            {
                "tab": "stocks",
                "sectionId": "sub-portfolio",  # HTML id (선택)
                "label": "내 포트폴리오",
                "items": ["TSLA $248.50 (+2.3%)", "PLTR $89.20 (-1.1%)"]
            },
            {
                "tab": "stocks",
                "sectionId": "sub-watchlist",
                "label": "관심종목",
                "items": ["AMZN $198.30 (+0.5%)"]
            }
        ]
    )

각 필드 설명:
    task_id   : 스케줄 태스크 ID (예: "kr-market-dashboard-update")
    updates   : 업데이트된 섹션 목록
      - tab       : 탭 ID ("overview", "stocks", "macro", "insight", "hotissue", "sources")
      - sectionId : HTML 요소 ID (예: "sub-portfolio", "sub-ceotracker") — 섹션 제목에 뱃지 표시
      - label     : 섹션 한글 이름 (예: "내 포트폴리오")
      - items     : 업데이트된 아코디언 항목 목록 (헤더 텍스트에서 매칭하여 뱃지 표시)
                    예: ["HD현대일렉트릭 ₩458,000", "Elon Musk 38%"]
"""

import json
import re
from datetime import datetime


def add_update_log(html_path: str, task_id: str, updates: list, max_entries: int = 50):
    """
    대시보드 HTML의 __updateLog 배열에 새 기록을 추가합니다.

    Args:
        html_path: 대시보드 HTML 파일 경로
        task_id: 스케줄 태스크 ID
        updates: 업데이트 섹션 목록 (위 docstring 참조)
        max_entries: 최대 보관 기록 수 (기본 50, 초과 시 오래된 것 삭제)
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 현재 __updateLog 배열 찾기
    pattern = r'var __updateLog\s*=\s*(\[[\s\S]*?\]);'
    match = re.search(pattern, content)

    if not match:
        print(f"⚠️ __updateLog 변수를 찾을 수 없습니다: {html_path}")
        return False

    try:
        current_log = json.loads(match.group(1))
    except json.JSONDecodeError:
        current_log = []

    # 새 엔트리 생성
    new_entry = {
        "taskId": task_id,
        "time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "updates": updates
    }

    # 추가 및 오래된 기록 정리
    current_log.append(new_entry)
    if len(current_log) > max_entries:
        current_log = current_log[-max_entries:]

    # JSON 직렬화 (한글 유지, 컴팩트)
    new_json = json.dumps(current_log, ensure_ascii=False, separators=(',', ':'))

    # HTML에 반영
    new_var = f'var __updateLog = {new_json};'
    content = re.sub(pattern, new_var, content)

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # 요약 출력
    total_items = sum(len(u.get('items', [])) for u in updates)
    print(f"✅ 업데이트 로그 기록 완료:")
    print(f"   태스크: {task_id}")
    print(f"   시간: {new_entry['time']}")
    print(f"   섹션: {len(updates)}개, 항목: {total_items}개")
    for u in updates:
        items_preview = ', '.join(u.get('items', [])[:3])
        if len(u.get('items', [])) > 3:
            items_preview += f" ... (+{len(u['items'])-3}개)"
        print(f"   📌 {u.get('label', '?')}: {items_preview}")

    return True


# 편의 함수: 자주 쓰이는 패턴
def log_stock_price_update(html_path, task_id, tab, section_id, section_label, stock_updates):
    """
    주가 업데이트 기록 편의 함수

    stock_updates: [("TSLA", "$248.50", "+2.3%"), ("PLTR", "$89.20", "-1.1%")]
    """
    items = [f"{name} {price} ({change})" for name, price, change in stock_updates]
    return add_update_log(html_path, task_id, [{
        "tab": tab,
        "sectionId": section_id,
        "label": section_label,
        "items": items
    }])


def log_multi_section_update(html_path, task_id, sections):
    """
    여러 섹션 한번에 기록

    sections: [
        ("macro", "bond-section", "채권/금리", ["미국 10년물 4.28%", "한국 3년물 2.85%"]),
        ("macro", "commodity-section", "원자재", ["WTI $67.2", "금 $2,985"]),
    ]
    """
    updates = [{
        "tab": tab,
        "sectionId": sec_id,
        "label": label,
        "items": items
    } for tab, sec_id, label, items in sections]
    return add_update_log(html_path, task_id, updates)


if __name__ == "__main__":
    # 테스트용 — 직접 실행 시 샘플 데이터 추가
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        html = sys.argv[2] if len(sys.argv) > 2 else "주식시장_대시보드.html"
        add_update_log(html, "kr-market-dashboard-update", [
            {
                "tab": "stocks",
                "sectionId": "sub-portfolio",
                "label": "내 포트폴리오",
                "items": ["TSLA $248.50 (+2.3%)", "PLTR $89.20 (-1.1%)", "HD현대일렉트릭 ₩458,000 (+1.8%)"]
            },
            {
                "tab": "stocks",
                "sectionId": "sub-watchlist",
                "label": "관심종목",
                "items": ["AMZN $198.30 (+0.5%)", "JOBY $7.85 (-2.1%)"]
            }
        ])
        print("\n테스트 데이터가 추가되었습니다.")
