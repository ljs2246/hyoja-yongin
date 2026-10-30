#!/usr/bin/env python3
"""공식 자료 갱신 관문(격리 규칙): 새로 받은 data/emergency.json·pharmacy.json 이 이상하면 이전 승인본으로 되돌린다(고객 화면에 올리지 않음).
검사: JSON 형식, '목록' 존재, 건수 일치, 기관명 필수, 이전 대비 급감(50% 미만) 금지, 기관 번호 형식(휴대전화·유료번호 금지). 사용: check-data.py [--restore]"""
import json,subprocess,sys,re
restore='--restore' in sys.argv;bad=[]
for f in ['data/emergency.json','data/pharmacy.json']:
    try:
        d=json.load(open(f));L=d['목록'];assert isinstance(L,list) and L
        if d.get('건수') not in(None,len(L)):bad.append((f,f'건수 불일치 {d.get("건수")} != {len(L)}'))
        if any(not x.get('dutyName') for x in L):bad.append((f,'기관명 없는 항목'))
        n=sum(1 for x in L if re.match(r'^(01\d|060|080|700)',re.sub(r'\D','',str(x.get('dutyTel1','')))))
        if n:bad.append((f,f'기관 번호로 부적절한 형식 {n}건'))
        try:
            old=json.loads(subprocess.run(['git','show','HEAD:'+f],capture_output=True,text=True,check=True).stdout)['목록']
            if len(L)<len(old)*0.5:bad.append((f,f'건수 급감 {len(old)}→{len(L)}'))
        except Exception:pass
    except Exception as e:bad.append((f,'읽기·형식 오류 '+type(e).__name__))
for f,m in bad:print('자료 검사 실패:',f,m)
if bad and restore:
    for f in {b[0] for b in bad}:subprocess.run(['git','checkout','--',f]);print('이전 승인본으로 복구:',f)
print('자료 검사','통과' if not bad else f'실패 {len(bad)}건');sys.exit(1 if bad and not restore else 0)
