#!/usr/bin/env python3
"""약국 전화번호 검증대장. 번호는 삭제하지 않고 보존하며, 공개 상태는 '공식 확인 → 공개 승인'을 거친 것만 '공개승인'.
사용: python3 scripts/pharmacy-phone-ledger.py build  (대장 갱신: 기존 상태 유지, 새 번호는 '미확인·숨김'으로 추가, 사라진 번호도 지우지 않고 '자료에서 사라짐' 표시)
      python3 scripts/pharmacy-phone-ledger.py check  (검사: 모든 약국 번호가 대장에 있고, 화면 승인 목록과 대장의 '공개승인'이 정확히 같을 것)"""
import json,re,sys,os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));LED=os.path.join(ROOT,'docs','pharmacy-phone-ledger.json')
def digits(v):return re.sub(r'\D','',str(v or ''))
def load_ledger():
    if os.path.exists(LED):return json.load(open(LED,encoding='utf-8'))
    return {'설명':'약국 전화번호 검증대장(번호는 삭제하지 않음). 상태: 미확인·숨김 / 공식확인·승인대기 / 공개승인 / 자료에서 사라짐','목록':[]}
def approved_in_js():
    s=open(os.path.join(ROOT,'medical-maps.js'),encoding='utf-8').read()
    m=re.search(r'PHARMACY_PHONE_APPROVED=\[(.*?)\]',s,re.S)
    return sorted(re.findall(r"'(\d+)'",m.group(1))) if m else None
def build():
    data=json.load(open(os.path.join(ROOT,'data','pharmacy.json'),encoding='utf-8'))
    led=load_ledger();idx={(r['약국'],r['주소'],r['번호']):r for r in led['목록']};seen=set()
    for p in data['목록']:
        num=digits(p.get('dutyTel1'));k=(p.get('dutyName',''),p.get('dutyAddr',''),num);seen.add(k)
        r=idx.get(k)
        if r is None:
            r={'약국':k[0],'주소':k[1],'번호':k[2],'원본표기':p.get('dutyTel1',''),'상태':'미확인·숨김','공식근거':None,'확인일':None,'승인자':None};led['목록'].append(r);idx[k]=r
        if r['상태']=='자료에서 사라짐':r['상태']='미확인·숨김'
    for k,r in idx.items():
        if k not in seen and r['상태']!='자료에서 사라짐':r['이전상태']=r['상태'];r['상태']='자료에서 사라짐'
    led['자료확인일']=data.get('확인한 때');led['건수']=len(led['목록'])
    json.dump(led,open(LED,'w',encoding='utf-8'),ensure_ascii=False,indent=1);print('대장 갱신:',led['건수'],'건')
def check():
    data=json.load(open(os.path.join(ROOT,'data','pharmacy.json'),encoding='utf-8'));led=load_ledger();bad=[]
    idx={(r['약국'],r['주소'],r['번호']):r for r in led['목록']}
    for p in data['목록']:  # 번호가 바뀌면 새 줄로 취급 → 새 번호는 승인 없음(미확인·숨김), 옛 줄은 보존
        if (p.get('dutyName',''),p.get('dutyAddr',''),digits(p.get('dutyTel1'))) not in idx:bad.append('대장에 없음(build 필요): '+str(p.get('dutyName')))
    appr=sorted({r['번호'] for r in led['목록'] if r['상태']=='공개승인'});js=approved_in_js()
    for r in led['목록']:
        if r['상태']=='공개승인' and not (r.get('공식근거') and r.get('승인자') and r.get('확인일')):bad.append('공개승인인데 근거·승인자·확인일 없음: '+r['약국'])
    if js is None:bad.append('medical-maps.js 승인 목록을 찾지 못함')
    elif js!=appr:bad.append(f'화면 승인 목록({len(js)})과 대장 공개승인({len(appr)})이 다름')
    if bad:print('실패:');[print(' -',b) for b in bad[:20]];sys.exit(1)
    st={};[st.__setitem__(r['상태'],st.get(r['상태'],0)+1) for r in led['목록']];print('통과: 대장',len(led['목록']),'건',st,'/ 화면 승인 목록',len(js),'건')
{'build':build,'check':check}.get(sys.argv[1] if len(sys.argv)>1 else '',lambda:print(__doc__))()
