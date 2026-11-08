# 효마음 데모 화면 모의검사 (Chromium 휴대폰 에뮬레이션). 실기기 시험이 아님. 실행: python3 tests/hyomaeum-e2e.py
import subprocess,time,json,sys,datetime,re
from playwright.sync_api import sync_playwright
R=[];PORT=8797
def rec(n,ok,note=''):R.append({'항목':n,'결과':'통과' if ok else '실패','비고':note});print('통과' if ok else '실패',n,note)
srv=subprocess.Popen(['python3','-m','http.server',str(PORT)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
U=f'http://localhost:{PORT}/lab/hyomaeum/index.html';K='hj-hyomaeum-v1'
def entries(pg):
    v=pg.evaluate(f"localStorage.getItem('{K}')");return [] if not v else [e for e in json.loads(v)['entries'] if not e['deleted_at'] and e['action_type']!='weeklyBonus']
try:
  with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(**p.devices['Pixel 5']);pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    reqs=[];pg.on('request',lambda r:reqs.append(r.url))
    pg.goto(U);pg.wait_for_selector('#optin')
    txt=pg.inner_text('body')
    rec('모1 첫 화면에 「돈이 아니에요」·자동 확인 불가·삭제 가능 안내가 보임','돈이나 상품권이 아니에요' in txt and '확인하지 못해요' in txt and '지울 수 있어요' in txt)
    rec('모2 사용을 선택하기 전에는 아무 것도 저장하지 않음',pg.evaluate(f"localStorage.getItem('{K}')") is None)
    pg.click('#optin');pg.wait_for_selector('#bCall')
    pg.click('#bCall');pg.wait_for_timeout(300)
    rec('모3 안부 전화 기록 → 50 적립, 버튼이 「기록했어요」로 바뀌고 눌리지 않음',len(entries(pg))==1 and pg.locator('#bCall').is_disabled() and '모인 마음 50' in pg.inner_text('#gardenInfo'))
    pg.reload();pg.wait_for_selector('#bCall')
    rec('모4 새로고침해도 유지되고 다시 적립되지 않음',len(entries(pg))==1 and pg.locator('#bCall').is_disabled())
    pg.evaluate("document.getElementById('bMsg').click();for(let i=0;i<10;i++)document.getElementById('bMsg').click()");pg.wait_for_timeout(500)
    rec('모5 연속 11번 클릭해도 메시지 기록은 1건',sum(1 for e in entries(pg) if e['action_type']=='msg')==1)
    # 두 창 동시
    pg2=ctx.new_page();pg2.goto(U);pg2.wait_for_selector('#bVisit')
    for q in (pg,pg2):q.wait_for_selector('#bVisit')
    pg.evaluate("setTimeout(()=>document.getElementById('bVisit').click(),50)");pg2.evaluate("setTimeout(()=>document.getElementById('bVisit').click(),50)")
    pg.wait_for_timeout(800)
    rec('모6 두 창에서 동시에 방문 기록을 눌러도 1건',sum(1 for e in entries(pg) if e['action_type']=='visit')==1,str(sum(1 for e in entries(pg) if e['action_type']=='visit')))
    pg2.close()
    before=len(entries(pg));pg.click('#fakeTel',no_wait_after=True);pg.wait_for_timeout(300)
    rec('모7 전화 링크만 누르면 효마음이 저절로 쌓이지 않음',len(entries(pg))==before)
    t0=pg.evaluate("JSON.parse(localStorage.getItem('%s')).entries.length"%K)
    pg.click('#bSkip');pg.wait_for_timeout(200)
    rec('모8 건너뛰기: 불이익·감점 없이 격려 문구, 기록 변화 없음','불이익은 없어요' in pg.inner_text('#msg') and pg.evaluate("JSON.parse(localStorage.getItem('%s')).entries.length"%K)==t0)
    keys=pg.evaluate("Object.keys(localStorage)");ck=ctx.cookies()
    ext=[r for r in reqs if not r.startswith(f'http://localhost:{PORT}/') and not r.startswith('tel:')]  # 전화 링크 이동은 외부 전송이 아님
    rec('모9 개인정보·외부 전송: 저장소 키 1개, 쿠키 0, 외부 요청 0',keys==[K] and not ck and not ext,f'{keys} {len(ck)} {len(ext)}')
    body=pg.inner_text('body')
    rec('모10 원화 환산·환급·현금화 표현 없음(「돈이 아니에요」 안내만)',not re.search(r'\d\s*(포인트|마음)\s*=|\d+\s*원|환급받|현금화|상품권으로 바꿔',body))
    fs=pg.evaluate("parseFloat(getComputedStyle(document.body).fontSize)");mh=pg.evaluate("Math.min(...[...document.querySelectorAll('button:not([hidden]),a.btn')].filter(e=>e.offsetParent).map(e=>e.getBoundingClientRect().height))")
    rec('모11 큰 글씨(기본 20px 이상)·버튼 높이 56px 이상',fs>=20 and mh>=56,f'{fs}px/{mh}px')
    sm=b.new_context(viewport={'width':320,'height':640});ps=sm.new_page();ps.goto(U);ps.evaluate(f"localStorage.setItem('{K}',JSON.stringify({{ver:1,enabled:true,anonymous_local_id:'aa',entries:[]}}))");ps.reload();ps.wait_for_selector('#bCall')
    rec('모12 320px 폭에서 가로 스크롤 없음',ps.evaluate("document.documentElement.scrollWidth<=document.documentElement.clientWidth"))
    sm.close()
    pg.click('#bOff');pg.wait_for_timeout(200)
    rec('모13 사용 그만두기 후에도 기록은 남고 「모든 기록 지우기」가 보임',len(entries(pg))>=1 and pg.locator('#bDelAll').is_visible())
    pg.click('#bDelAll');pg.wait_for_timeout(200)
    rec('모14 모든 기록 지우기 → 저장소에 아무것도 남지 않음',pg.evaluate(f"localStorage.getItem('{K}')") is None and pg.evaluate("Object.keys(localStorage).length")==0)
    # 시계: 한국시간 자정 경계
    c3=b.new_context(**p.devices['Pixel 5']);p3=c3.new_page()
    p3.clock.install(time=datetime.datetime(2026,11,2,14,59,50,tzinfo=datetime.timezone.utc))
    p3.goto(U);p3.evaluate(f"localStorage.setItem('{K}',JSON.stringify({{ver:1,enabled:true,anonymous_local_id:'bb',entries:[]}}))");p3.reload();p3.wait_for_selector('#bCall')
    p3.click('#bCall');p3.wait_for_timeout(200)
    ok1=p3.locator('#bCall').is_disabled()
    p3.clock.set_system_time(datetime.datetime(2026,11,2,15,0,5,tzinfo=datetime.timezone.utc));p3.reload();p3.wait_for_selector('#bCall');p3.wait_for_timeout(200)
    rec('모15 한국시간 자정(UTC 15:00)이 지나면 새 날로 다시 기록 가능',ok1 and not p3.locator('#bCall').is_disabled())
    rec('모16 화면 오류 0건',not errs,str(errs))
    c3.close()
finally:srv.terminate()
bad=[r for r in R if r['결과']=='실패'];print(f'\n효마음 화면 모의검사 {len(R)-len(bad)}/{len(R)} 통과')
json.dump(R,open('tests/hyomaeum-e2e-results.json','w'),ensure_ascii=False,indent=1);sys.exit(1 if bad else 0)
