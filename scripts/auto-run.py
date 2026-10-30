#!/usr/bin/env python3
"""자동화 1단계 실행기. 단계별로 실행하고 실행 기록(JSON)을 남기며, 실패하면 즉시 중단(이후 단계 미실행)하고 알림 파일을 만든다.
운영 배포·게시·결제는 하지 않는다(승인 필요). 사용: auto-run.py [--out DIR] [--branch-check]"""
import subprocess,json,sys,os,datetime,uuid,argparse
ap=argparse.ArgumentParser();ap.add_argument('--out',default='docs/runs');ap.add_argument('--root',default='.');a=ap.parse_args()
os.chdir(a.root);os.makedirs(a.out,exist_ok=True)
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
def sh(c):return subprocess.run(c,shell=True,capture_output=True,text=True)
commit=sh('git rev-parse --short HEAD').stdout.strip() or 'unknown'
branch=sh('git rev-parse --abbrev-ref HEAD').stdout.strip() or 'unknown'
STEPS=[
 ('02 정보 검증·격리 담당','전화 링크 공식근거 검사','python3 scripts/check-phones.py','화면 HTML 전체 tel 링크'),
 ('03 앱 개발·테스트 담당','가족 기능 단위검사','node tests/family.test.cjs','family.js'),
 ('03 앱 개발·테스트 담당','의료·지역 검사','node scripts/test-medical-maps.cjs && node scripts/test-region-core.cjs && node scripts/test-region-profiles.cjs','medical-maps/region 스크립트'),
 ('03 앱 개발·테스트 담당','휴대폰 화면 모의검사','python3 tests/e2e-mobile.py','Chromium 모의 기기 3종'),
]
run={'runId':now.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6],'startedKST':now.isoformat(timespec='seconds'),'branch':branch,'commit':commit,'approver':None,'deployed':False,'published':False,'steps':[],'status':'진행'}
if branch=='main': # 운영 main에서는 실행 자체를 거부
    run['status']='중단(운영 main 보호)';print('운영 main에서는 자동 실행하지 않습니다');
else:
    for dept,name,cmd,inp in STEPS:
        t=datetime.datetime.now();r=sh(cmd)
        st={'department':dept,'task':name,'input':inp,'command':cmd,'seconds':round((datetime.datetime.now()-t).total_seconds(),1),'result':'통과' if r.returncode==0 else '실패','tail':(r.stdout.strip().splitlines() or [''])[-1][:200]}
        if r.returncode: st['error']=(r.stderr.strip() or r.stdout.strip())[-400:]
        run['steps'].append(st);print(st['result'],name)
        if r.returncode: run['status']='자동 중단(실패)';break
    else: run['status']='전체 통과'
run['endedKST']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
f=os.path.join(a.out,f"run-{run['runId']}.json");json.dump(run,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
if run['status']!='전체 통과':
    al=os.path.join(a.out,f"ALERT-{run['runId']}.md")
    bad=[s for s in run['steps'] if s['result']=='실패']
    open(al,'w',encoding='utf-8').write(f"# 자동화 중단 알림\n\n- 실행 {run['runId']} / 브랜치 {branch} / 커밋 {commit}\n- 상태: {run['status']}\n- 실패 단계: {', '.join(s['task'] for s in bad) or '없음'}\n- 조치: 원인 수정 전까지 다음 단계·반영 금지. 복구: 수정 후 scripts/auto-run.py 재실행\n")
    print('알림 파일:',al)
print('실행 기록:',f,'상태:',run['status']);sys.exit(0 if run['status']=='전체 통과' else 1)
