#!/usr/bin/env python3
"""공식 자료 변경 탐지·격리 보고(읽기 전용): 직전 저장본과 현재 data/*.json 을 비교해 신규·삭제·번호 변경·시간 이상 기관을 찾는다.
번호가 바뀐 기관은 '격리 대기'로 표시(검수 승인 전까지 번호 노출 금지 후보). 데이터 파일을 바꾸지 않고 docs/changes-latest.json 만 쓴다. 사용: detect-changes.py [기준커밋]"""
import json,subprocess,sys,re,datetime
base=sys.argv[1] if len(sys.argv)>1 else None
def key(x):return x.get('hpid') or ((x.get('dutyName') or '')+'|'+(x.get('dutyAddr') or ''))
def tel(x):return re.sub(r'\D','',str(x.get('dutyTel1','')))
def old(f):
    ref=base
    if not ref:
        r=subprocess.run(['git','log','--format=%H','-n','2','--',f],capture_output=True,text=True).stdout.split()
        ref=r[1] if len(r)>1 else None
    if not ref:return None,None
    p=subprocess.run(['git','show',f'{ref}:{f}'],capture_output=True,text=True)
    return (json.loads(p.stdout)['목록'],ref[:8]) if p.returncode==0 else (None,None)
out={'생성':datetime.datetime.now().isoformat(timespec='seconds'),'파일':{}}
for f in ['data/emergency.json','data/pharmacy.json']:
    new=json.load(open(f))['목록'];prev,ref=old(f)
    if prev is None:out['파일'][f]={'비교':'기준 없음(첫 기록)'};continue
    N={key(x):x for x in new};P={key(x):x for x in prev}
    add=[k for k in N if k not in P];rem=[k for k in P if k not in N]
    chg=[{'기관':N[k].get('dutyName'),'이전번호':tel(P[k]),'새번호':tel(N[k]),'처리':'격리 대기(검수 승인 전 번호 노출 금지 후보)'} for k in N if k in P and tel(N[k])!=tel(P[k])]
    odd=[N[k].get('dutyName') for k in N if any(re.match('dutyTime',kk) and str(v)=='2500' for kk,v in N[k].items())]
    out['파일'][f]={'기준커밋':ref,'신규':len(add),'삭제':len(rem),'번호변경':chg,'비정상시간(2500)':len(odd),'긴급 영향':'있음' if f.endswith('emergency.json') and (add or rem or chg) else '없음'}
json.dump(out,open('docs/changes-latest.json','w'),ensure_ascii=False,indent=1)
for f,v in out['파일'].items():print(f,v if '비교' in v else f"신규 {v['신규']} 삭제 {v['삭제']} 번호변경 {len(v['번호변경'])} 비정상시간 {v['비정상시간(2500)']} 긴급영향 {v['긴급 영향']}")
