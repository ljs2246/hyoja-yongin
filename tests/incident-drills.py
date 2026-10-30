# 사고 모의훈련 3종 자동시험 (임시 복사본에서만 실행, 원본·main 불변)
# ① 근거 없는 의료번호 입력 차단  ② 같은 자동화 작업 두 번(동시 포함) 실행 시 중복 결과 0건  ③ 구버전 캐시 노출 방지(오프라인 포함)
import subprocess,tempfile,shutil,os,json,glob,time,sys
from playwright.sync_api import sync_playwright
ROOT=os.getcwd();R=[]
def rec(n,ok,note=''):R.append((n,ok));print('통과' if ok else '실패',n,note)
def sh(c,cwd,**k):return subprocess.run(c,shell=True,cwd=cwd,capture_output=True,text=True,**k)
def clone():
    d=tempfile.mkdtemp();subprocess.run(f"tar --exclude=.git --exclude=node_modules --exclude=docs/runs -cf - . | tar -xf - -C {d}",shell=True,cwd=ROOT)
    sh("git init -q . && git add -A >/dev/null && git -c user.email=t@t -c user.name=t commit -qm t && git checkout -qb test/drill",d);return d
# ── 훈련 1 ──
d=clone()
sh("echo '<a href=\"tel:0319990000\">미확인 병원 031-999-0000</a>' >> Emergency.html",d)
rec('훈련1-a 근거 없는 병원 번호 링크가 들어오면 전화근거 검사가 실패(차단)',sh('python3 scripts/check-phones.py',d).returncode!=0)
d1=clone()
rec('훈련1-b 형식 검사(휴대전화·유료번호 거부)',sh('node scripts/test-medical-maps.cjs',d1).returncode==0)
srv=subprocess.Popen(['python3','-m','http.server','8793'],cwd=d1,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
  with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_context(**p.devices['Pixel 5']).new_page()
    pg.goto('http://localhost:8793/Emergency.html');pg.wait_for_timeout(800)
    out=pg.evaluate("[window.hjMedicalMaps.phone('010-9999-8888'),window.hjMedicalMaps.phone('060-700-1234'),window.hjMedicalMaps.phone('031-300-0114')]")
    rec('훈련1-c 브라우저에서도 휴대전화·유료번호는 거부, 정상 기관번호만 통과',out==[None,None,'0313000114'],str(out))
    # 동적으로 그려지는 약국 전화 링크에도 출처·확인일 속성이 붙는지
    pg.select_option('select',index=1) if pg.locator('select').count() else None
    pg.wait_for_timeout(1200)
    links=pg.eval_on_selector_all('#list a[href^="tel:"], a[href^="tel:"]','e=>e.map(a=>[a.hasAttribute("data-hj-src"),a.getAttribute("data-hj-checked")])')
    rec('훈련1-d 화면의 모든 전화 링크에 출처·확인일 표시(동적 약국 포함)',all(s and c for s,c in links),f'{len(links)}개')
    # ── 훈련 3 ──
    pg=b.new_context(**p.devices['Pixel 5']).new_page()  # 서비스워커가 없는 새 기기처럼 시작
    pg.goto('http://localhost:8793/manifest.webmanifest')
    pg.evaluate("caches.open('hyoja-v40').then(c=>c.put('/Emergency.html',new Response('<p>OLD tel:03100000000 EXPIRED</p>')))")
    pg.goto('http://localhost:8793/Emergency.html');pg.wait_for_timeout(3500);pg.reload();pg.wait_for_timeout(1500)
    keys=pg.evaluate('caches.keys()')
    rec('훈련3-a 갱신 후 구버전 캐시 삭제',all(k.startswith('hyoja-v') and k!='hyoja-v40' for k in keys),str(keys))
    rec('훈련3-b 화면에 구버전 번호·만료 문구 없음','OLD' not in pg.content() and '03100000000' not in pg.content())
    ctx=pg.context;ctx.set_offline(True);pg.reload();pg.wait_for_timeout(1500)
    rec('훈련3-c 오프라인에서도 옛 자료가 아닌 최신 캐시 화면(번호 링크 정상) 표시','03151899001' in pg.content() and 'OLD' not in pg.content())
finally:srv.terminate()
# ── 훈련 4(추가): 임시 차단 스위치 ──
d4=clone();open(d4+'/data/killswitch.json','w').write('{"active":true,"hide":["a[data-hj-src^=\'공공데이터\']","a[href=\'tel:15771122\']"],"notice":"점검 중"}')
srv=subprocess.Popen(['python3','-m','http.server','8794'],cwd=d4,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
  with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_context(**p.devices['Pixel 5']).new_page();pg.goto('http://localhost:8794/Emergency.html');pg.wait_for_timeout(1500)
    vis=lambda s:pg.locator(s).first.is_visible() if pg.locator(s).count() else False
    rec('훈련4-a 스위치 켜면 지정 항목(1577-1122)이 숨겨지고 안내 문구 표시',not vis('a[href="tel:15771122"]') and pg.locator('[data-hj-killswitch-notice]').count()==1)
    rec('훈련4-b 스위치가 켜져도 119는 계속 보임',vis('a[href="tel:119"]'))
    d4b=clone();srv2=subprocess.Popen(['python3','-m','http.server','8795'],cwd=d4b,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
    pg2=b.new_context(**p.devices['Pixel 5']).new_page();pg2.goto('http://localhost:8795/Emergency.html');pg2.wait_for_timeout(1500)
    rec('훈련4-c 기본값(꺼짐)에서는 아무것도 숨기지 않음',pg2.locator('a[href="tel:15771122"]').first.is_visible() and pg2.locator('[data-hj-killswitch-notice]').count()==0);srv2.terminate();shutil.rmtree(d4b,ignore_errors=True)
finally:srv.terminate();shutil.rmtree(d4,ignore_errors=True)
# ── 훈련 5(추가): 공식 자료 갱신 관문 ──
d5=clone();orig=open(d5+'/data/pharmacy.json').read()
j=json.loads(orig);j['목록']=j['목록'][:3];j['건수']=3;open(d5+'/data/pharmacy.json','w').write(json.dumps(j,ensure_ascii=False))
r=sh('python3 scripts/check-data.py',d5)
rec('훈련5-a 자료가 급감하면 자료 검사가 실패(차단)',r.returncode!=0,r.stdout.strip().splitlines()[0] if r.stdout else '')
sh('python3 scripts/check-data.py --restore',d5)
rec('훈련5-b 복구 옵션이 이전 승인본으로 되돌림(고객 화면 반영 안 됨)',open(d5+'/data/pharmacy.json').read()==orig)
j=json.loads(orig);j['목록'][0]['dutyTel1']='010-1111-2222';open(d5+'/data/pharmacy.json','w').write(json.dumps(j,ensure_ascii=False))
rec('훈련5-c 기관 번호가 휴대전화 형식이면 자료 검사가 실패',sh('python3 scripts/check-data.py',d5).returncode!=0);shutil.rmtree(d5,ignore_errors=True)
# ── 훈련 2 ──
d2=clone()
procs=[subprocess.Popen(f"python3 scripts/auto-run.py --out {d2}/runs",shell=True,cwd=d2,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True) for _ in range(2)]
outs=[(q.communicate()[0],q.returncode) for q in procs]
codes=sorted(c for _,c in outs);n1=len(glob.glob(d2+'/runs/run-*.json'))
rec('훈련2-a 동시에 두 번 실행해도 실제 실행은 1건(나머지는 잠금 차단)',n1==1 and 2 in codes,f'기록 {n1}건 종료코드 {codes}')
sh(f"python3 scripts/auto-run.py --out {d2}/runs",d2);n2=len(glob.glob(d2+'/runs/run-*.json'))
rec('훈련2-b 통과한 작업을 다시 실행해도 새 결과 0건(중복 방지)',n2==n1,f'{n1}→{n2}')
ids={json.load(open(f))['taskId'] for f in glob.glob(d2+'/runs/run-*.json')}
rec('훈련2-c 작업번호(taskId) 1개로 고정',len(ids)==1)
for x in (d,d1,d2):shutil.rmtree(x,ignore_errors=True)
bad=[n for n,o in R if not o];print(f'\n모의훈련 {len(R)-len(bad)}/{len(R)} 통과');json.dump([{'항목':n,'결과':'통과' if o else '실패'} for n,o in R],open('tests/incident-drills-results.json','w'),ensure_ascii=False,indent=1);sys.exit(1 if bad else 0)
