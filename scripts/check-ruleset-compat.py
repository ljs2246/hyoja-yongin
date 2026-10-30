#!/usr/bin/env python3
"""main 보호 규칙 준비본이 기존 자동 갱신 흐름과 충돌하지 않는지 사전 점검(적용 전 정적 검사).
검사: ① main 에 직접 push 하는 워크플로우 단계 없음 ② 규칙이 요구하는 필수 검사 이름이 실제 작업 이름과 일치 ③ 그 작업이 PR 사용자 실행과 수동 실행 둘 다 가능 ④ 갱신 흐름이 qa 를 직접 요청 ⑤ 우회 허용 주체 없음 ⑥ push 하는 쪽에 contents 쓰기 권한 외 불필요한 권한 없음. 사용법: check-ruleset-compat.py [워크플로우폴더] [규칙 JSON]"""
import sys,glob,json,re,yaml,os
wf=sys.argv[1] if len(sys.argv)>1 else '.github/workflows';rs=sys.argv[2] if len(sys.argv)>2 else 'docs/security/main-ruleset-proposal.json'
bad=[];info=[]
R=json.load(open(rs));req=[c['context'] for x in R['rules'] if x['type']=='required_status_checks' for c in x['parameters']['required_status_checks']]
if R.get('bypass_actors'):bad.append('우회 허용 주체가 있음')
W={}
for f in glob.glob(wf+'/*.yml'):
    y=yaml.safe_load(open(f));W[os.path.basename(f)]=y
    on=y.get(True,y.get('on',{})) # yaml 이 on 을 True 로 읽는 경우 대응
    for jn,j in (y.get('jobs') or {}).items():
        for s in j.get('steps',[]) or []:
            run=s.get('run','') or ''
            for m in re.finditer(r'git push([^\n;&|]*)',run):
                a=m.group(1).strip(' )"\'') or '(대상 미지정, 현재 브랜치)'
                if not a or re.search(r'\b(origin\s+)?(HEAD:)?(refs/heads/)?main\b',a) or re.fullmatch(r'(-q\s+)?',a) or 'origin' not in a:
                    bad.append(f'{os.path.basename(f)}: main 으로 가는 직접 push 가능성 → "git push {a}"')
                else:info.append(f'{os.path.basename(f)}: git push {a} (갱신 브랜치 변수 사용)')
            if 'auto-data-pr.sh' in run:info.append(f'{os.path.basename(f)}: 갱신은 scripts/auto-data-pr.sh(브랜치 push+PR)')
# 필수 검사 이름 ↔ 실제 작업
qa=None
for fn,y in W.items():
    on=y.get(True,y.get('on',{})) or {}
    for jn,j in (y.get('jobs') or {}).items():
        if (j.get('name') or jn) in req:
            qa=(fn,jn,on)
for c in req:
    if not qa:bad.append(f'필수 검사 "{c}" 와 같은 이름의 작업이 없음 → 병합이 영원히 막힘')
if qa:
    fn,jn,on=qa
    if 'pull_request' not in on:bad.append(f'{fn}: 사람이 만든 PR에서 qa 가 자동 실행되지 않음(pull_request 없음)')
    if 'workflow_dispatch' not in on:bad.append(f'{fn}: 자동 생성 PR용 수동 실행(workflow_dispatch)이 없음')
    info.append(f'필수 검사 {req} = {fn} 의 작업 {jn} (PR·수동 실행 가능)')
# 갱신 워크플로우가 qa 를 요청할 수 있어야 함
for fn,y in W.items():
    if any('auto-data-pr.sh' in (s.get('run','') or '') for j in (y.get('jobs') or {}).values() for s in (j.get('steps') or [])):
        p=y.get('permissions') or {}
        if p.get('actions')!='write':bad.append(f'{fn}: 갱신 흐름에 actions: write 가 없어 qa 실행 요청 불가')
        if p.get('contents')!='write' or p.get('pull-requests')!='write':bad.append(f'{fn}: 갱신 브랜치 push/PR 권한 부족')
        if any(v=='write' for k,v in p.items() if k not in('contents','pull-requests','actions')):bad.append(f'{fn}: 불필요한 쓰기 권한')
for i in info:print('확인:',i)
for b in bad:print('충돌:',b)
print('보호 규칙 호환 점검','통과' if not bad else f'충돌 {len(bad)}건');sys.exit(1 if bad else 0)
