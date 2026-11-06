#!/usr/bin/env python3
"""응급의료기관 전화 허용목록 검사: (1) medical-maps.js 의 EMERGENCY_PHONE_APPROVED 와 docs/phone-allowlist.json 이 정확히 같을 것
(2) 허용목록 항목은 필수 필드가 모두 있고 번호가 phone-policy-log.json 의 '유지' 번호와 일치할 것 (3) 허용 번호가 현재 data/emergency.json 의 번호와 달라졌다면 알림(자료 변경 감지)"""
import json,re,sys
al=json.load(open('docs/phone-allowlist.json',encoding='utf-8'));bad=[]
js=open('medical-maps.js',encoding='utf-8').read();m=re.search(r"EMERGENCY_PHONE_APPROVED=\{(.*?)\};",js,re.S)
cur={}
if m:
    for h,arr in re.findall(r"'(A\d+)':\[(.*?)\]",m.group(1)):cur[h]=sorted(re.findall(r"'(\d+)'",arr))
else:bad.append('medical-maps.js 에서 허용목록을 찾지 못함')
exp={}
for x in al['목록']:exp.setdefault(x['hpid'],[]).append(x['번호'])
exp={k:sorted(v) for k,v in exp.items()}
if cur!=exp:bad.append(f'화면 허용목록과 JSON이 다름: JS={cur} JSON={exp}')
need=['기관명','hpid','번호','용도','공식원문URL','원문확인일','검증일','검증상태','검증자']
pol={x['number'] for x in json.load(open('docs/phone-policy-log.json',encoding='utf-8')) if str(x.get('action','')).startswith('유지')}
for x in al['목록']:
    for k in need:
        if not x.get(k):bad.append(f"{x.get('기관명')}: 필드 {k} 없음")
    if x['번호'] not in pol:bad.append(f"{x['기관명']}: 번호 {x['번호']} 가 정책 로그의 '유지' 번호에 없음")
data={x['hpid']:re.sub(r'\D','',str(x.get('dutyTel1',''))) for x in json.load(open('data/emergency.json',encoding='utf-8'))['목록']}
for x in al['목록']:
    if data.get(x['hpid']) and data[x['hpid']]!=x['번호']:print('알림(실패 아님): 공공데이터 번호가 허용 번호와 다름 →',x['기관명'],data[x['hpid']],'(허용 번호 유지, 사람 확인 필요)')
for b in bad:print('실패:',b)
print('허용목록 검사','통과' if not bad else f'실패 {len(bad)}건','(허용 기관',len(al['목록']),'곳)');sys.exit(1 if bad else 0)
