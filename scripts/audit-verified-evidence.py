#!/usr/bin/env python3
"""기존 공식기관 원문 재검사 기록 vs 고객 노출 정책의 일치 여부만 검증.
새로운 공식 웹페이지를 실시간 확인한 결과가 아님. 고객 자료/운영 서버 수정 없음.
"""
import json
import pathlib
import sys
from collections import Counter

ROOT=pathlib.Path(__file__).resolve().parents[1]
urls=json.loads((ROOT/"docs/url-recheck-20261030.json").read_text(encoding="utf-8"))
policies=json.loads((ROOT/"docs/phone-policy-log.json").read_text(encoding="utf-8"))
errors=[]
status=Counter()
def normalize(num):
    return "".join(ch for ch in str(num) if ch.isdigit())
by_number={}
for p in policies:
    by_number.setdefault(normalize(p.get("number","")),[]).append(p)
    action=str(p.get("action",""))
    if action.startswith("유지"):status["유지"]+=1
    elif action.startswith("숨김"):status["숨김"]+=1
    else:errors.append("알 수 없는 정책 상태: "+str(p.get("agency"))+" "+action)

source_checks=Counter()
for entry in urls:
    n=normalize(entry.get("number",""))
    # 동일 번호가 여러 기관·페이지에 등장할 수 있으므로
    # 미확인 건은 연결된 정책 중 해당 기관의 조치가 숨김인지 검사.
    rows=[p for p in by_number.get(n,[]) if p.get("agency")==entry.get("agency")]
    if not rows:
        errors.append(f"정책 행 없음: {entry.get('agency')} {n}")
        continue
    if entry.get("found"):
        source_checks["기존 기록 확인"]+=1
    else:
        source_checks["기존 기록 미확인"]+=1
        if any(not str(p.get("action","")).startswith("숨김") for p in rows):
            errors.append(f"공식 원문 미확인 번호 노출 정책 위험: {entry.get('agency')} {n}")
        print(f"보류: {entry.get('agency')} ({n}) / 공식 원문 현재 근거 미확정")

# source verify must not silently convert the old evidence to a current check.
for p in policies:
    if str(p.get("action","")).startswith("유지"):
        if not p.get("sourceUrl") or not p.get("checked"):
            errors.append("공개 유지인데 공식 출처/확인일 없음: "+str(p.get("agency")))

for e in errors:print("검수 실패:",e)
print("기존 URL 기록",len(urls),"건:",dict(source_checks))
print("전화 정책",len(policies),"건:",dict(status))
print("※ 과거 원문 대조 기록에 대한 내부 정합성 검사이며 실제 웹/영업 여부 재확인 아님.")
sys.exit(1 if errors else 0)
