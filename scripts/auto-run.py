#!/usr/bin/env python3
"""자동화 1단계 실행기. 단계별로 실행하고 실행 기록(JSON)을 남기며, 실패하면 즉시 중단(이후 단계 미실행)하고 알림 파일을 만든다.
운영 배포·게시·결제는 하지 않는다(승인 필요). 사용: auto-run.py [--out DIR] [--branch-check]"""
import subprocess,json,sys,os,datetime,uuid,argparse,hashlib,glob,fcntl,tempfile
ap=argparse.ArgumentParser();ap.add_argument('--out',default='docs/runs');ap.add_argument('--root',default='.');ap.add_argument('--force',action='store_true');a=ap.parse_args()
os.chdir(a.root);os.makedirs(a.out,exist_ok=True)
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
def sh(c,timeout=None):
    try:return subprocess.run(c,shell=True,capture_output=True,text=True,timeout=timeout)
    except subprocess.TimeoutExpired:return subprocess.CompletedProcess(c,124,'','시간 초과(무한 반복 방지로 강제 종료)')
STEP_TIMEOUT=600;RETRY={'python3 tests/e2e-mobile.py':1,'python3 tests/hyomaeum-e2e.py':1}  # 단계별 제한시간 10분, 브라우저 시험만 1회 재시도(최대 2회)
# 동일 작업 번호(taskId): 커밋+수정내용+단계 목록이 같으면 같은 작업. 이미 통과한 작업은 다시 만들지 않는다.
def task_id():
    ex=[os.path.relpath(a.out).rstrip('/'),'docs/runs']  # 실행 기록 폴더 자체는 작업 내용에 포함하지 않음
    pat='|'.join('^'+e+'/' for e in ex)+'|e2e-mobile-results|hyomaeum-e2e-results|incident-drills-results|docs/changes-latest.json|docs/automation/work-board.md'
    d=sh("git diff HEAD --name-only | grep -Ev '"+pat+"'; git ls-files -o --exclude-standard | grep -Ev '"+pat+"'").stdout
    d+=sh("git diff HEAD -- . "+' '.join("':!"+e+"'" for e in ex)+" ':!tests/e2e-mobile-results.json' ':!tests/incident-drills-results.json' ':!tests/hyomaeum-e2e-results.json' ':!docs/changes-latest.json' ':!docs/automation/work-board.md'").stdout
    return hashlib.sha1((sh('git rev-parse HEAD').stdout+d+'|'.join(s[1] for s in STEPS)).encode()).hexdigest()[:12]
commit=sh('git rev-parse --short HEAD').stdout.strip() or 'unknown'
branch=sh('git rev-parse --abbrev-ref HEAD').stdout.strip() or 'unknown'
STEPS=[
 ('02 정보 검증·격리 담당','전화 링크 공식근거 검사','python3 scripts/check-phones.py','화면 HTML 전체 tel 링크'),
 ('05 구글 드라이브 문서관리 담당','드라이브 업로더 안전장치 시험(가짜 서버)','python3 tests/drive-upload.test.py','scripts/drive-upload.py'),
 ('02 정보 검증·격리 담당','공식 자료 갱신 관문 검사','python3 scripts/check-data.py','data/emergency.json·pharmacy.json'),
 ('02 정보 검증·격리 담당','공식 자료 변경 탐지 보고(읽기 전용)','python3 scripts/detect-changes.py','data/*.json 직전 저장본과 비교'),
 ('09 일정·회계·경영 보고 담당','작업 현황 통합 관리표 검사','python3 scripts/work-board.py','docs/automation/work-board.json'),
 ('02 정보 검증·격리 담당','공식정보 근거·확인일 신선도 검사','python3 scripts/check-freshness.py','docs/phone-policy-log.json'),
 ('06 운영·보안 담당','보안 검사(비밀정보·외부 스크립트·권한)','python3 scripts/check-security.py','저장소 전체 파일'),
 ('06 운영·보안 담당','보호 규칙·자동 갱신 흐름 충돌 사전 점검','python3 scripts/check-ruleset-compat.py','.github/workflows'),
 ('02 정보 검증·격리 담당','격리 자료(일반 병원) 고객 화면 노출 차단 점검','python3 scripts/check-staging.py','data/staging'),
 ('03 앱 개발·테스트 담당','접근성·고령친화 정적 검사','python3 scripts/check-a11y.py','화면 HTML 전체'),
 ('03 앱 개발·테스트 담당','효마음 데모 단위검사(격리 기능)','node tests/hyomaeum.test.cjs','lab/hyomaeum/hyomaeum-core.js'),
 ('03 앱 개발·테스트 담당','가족 기능 단위검사','node tests/family.test.cjs','family.js'),
 ('03 앱 개발·테스트 담당','의료·지역 검사','node scripts/test-medical-maps.cjs && node scripts/test-region-core.cjs && node scripts/test-region-profiles.cjs','medical-maps/region 스크립트'),
 ('03 앱 개발·테스트 담당','효마음 데모 화면 모의검사','python3 tests/hyomaeum-e2e.py','Chromium 모의 기기'),
 ('03 앱 개발·테스트 담당','휴대폰 화면 모의검사','python3 tests/e2e-mobile.py','Chromium 모의 기기 3종'),
]
TID=task_id()
DIRTY=bool(sh("git status --porcelain | grep -v ' docs/runs/' | grep -v e2e-mobile-results | grep -v changes-latest | grep -v work-board.md").stdout.strip())  # 커밋되지 않은 수정이 있으면 복구 후보로 인정하지 않음
run={'dirty':DIRTY,'taskId':TID,'runId':now.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6],'startedKST':now.isoformat(timespec='seconds'),'branch':branch,'commit':commit,'approver':None,'deployed':False,'published':False,'steps':[],'status':'진행'}
lock=open(os.path.join(tempfile.gettempdir(),'hyoja-auto-run.lock'),'w')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except OSError:print('다른 자동 실행이 진행 중입니다. 중복 실행을 차단했습니다.');sys.exit(2)
prev=[f for f in glob.glob(os.path.join(a.out,'run-*.json')) if (lambda j:j.get('taskId')==TID and j.get('status')=='전체 통과')(json.load(open(f)))]
if prev and not a.force and branch!='main':
    print('중복 방지: 같은 작업번호',TID,'는 이미 통과했습니다 →',prev[-1],'(다시 실행하려면 --force)');sys.exit(0)
if branch=='main' and os.environ.get('HJ_ALLOW_MAIN_READONLY')!='1': # 운영 main에서는 실행 자체를 거부
    run['status']='중단(운영 main 보호)';print('운영 main에서는 자동 실행하지 않습니다');
else:
    for dept,name,cmd,inp in STEPS:
        t=datetime.datetime.now();r=sh(cmd,STEP_TIMEOUT);tries=1
        while r.returncode and tries<=RETRY.get(cmd,0):r=sh(cmd,STEP_TIMEOUT);tries+=1
        st={'department':dept,'task':name,'input':inp,'command':cmd,'attempts':tries,'seconds':round((datetime.datetime.now()-t).total_seconds(),1),'result':'통과' if r.returncode==0 else '실패','tail':(r.stdout.strip().splitlines() or [''])[-1][:200]}
        if r.returncode: st['error']=(r.stderr.strip() or r.stdout.strip())[-400:]
        run['steps'].append(st);print(st['result'],name)
        if r.returncode: run['status']='자동 중단(실패)';break
    else: run['status']='전체 통과'
run['endedKST']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
f=os.path.join(a.out,f"run-{run['runId']}.json");json.dump(run,open(f+'.tmp','w',encoding='utf-8'),ensure_ascii=False,indent=1);os.replace(f+'.tmp',f)  # 쓰기 성공 후에만 등록(원자적 저장)
if run['status']!='전체 통과':
    al=os.path.join(a.out,f"ALERT-{run['runId']}.md")
    bad=[s for s in run['steps'] if s['result']=='실패']
    open(al,'w',encoding='utf-8').write(f"# 자동화 중단 알림\n\n- 실행 {run['runId']} / 브랜치 {branch} / 커밋 {commit}\n- 상태: {run['status']}\n- 실패 단계: {', '.join(s['task'] for s in bad) or '없음'}\n- 조치: 원인 수정 전까지 다음 단계·반영 금지. 복구: 수정 후 scripts/auto-run.py 재실행\n")
    print('알림 파일:',al)
print('실행 기록:',f,'상태:',run['status']);sys.exit(0 if run['status']=='전체 통과' else 1)
