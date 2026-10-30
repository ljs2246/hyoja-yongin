#!/usr/bin/env python3
"""공식정보 신선도·근거 검사: 노출(유지) 번호는 기관·공식 URL·확인일이 모두 있어야 하고, 확인일이 기준보다 오래되면 실패.
응급·의료 번호는 30일, 그 외는 90일. 숨김 항목은 화면에 없는지만 다른 검사가 확인한다."""
import json,sys,datetime,re
today=datetime.date.today();bad=[]
log=json.load(open('docs/phone-policy-log.json'))
for x in log:
    if x['action']=='숨김':continue
    k=f"{x['page']} {x['number']}"
    if not x.get('agency'):bad.append((k,'기관명 없음'))
    if not (x.get('sourceUrl') or '').startswith(('http','data/')):bad.append((k,'공식 URL(또는 공공데이터 파일) 없음'))
    try:d=datetime.date.fromisoformat(x.get('checked',''))
    except Exception:bad.append((k,'확인일 형식 오류'));continue
    strict=x['page']=='Emergency.html' or x.get('category') in('응급','의료') or re.fullmatch(r'11[29]',x['number'])
    lim=30 if strict else 90
    if (today-d).days>lim:bad.append((k,f'확인일 {x["checked"]} 이(가) {lim}일 초과'))
    if (today-d).days<0:bad.append((k,'확인일이 미래'))
for k,m in bad:print('신선도 검사 실패:',k,m)
print('신선도 검사','통과' if not bad else f'실패 {len(bad)}건');sys.exit(1 if bad else 0)
