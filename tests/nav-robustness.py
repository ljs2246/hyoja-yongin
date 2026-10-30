# 메뉴 이동 중 중복 실행·오류 점검 (Chromium 모의 기기): 빠른 연속 누름, 무작위 이동 40회, 뒤로 가기, 오프라인 이동, 가족 저장 중복
# 실행: python3 tests/nav-robustness.py   결과: tests/nav-robustness-results.json
import subprocess,time,json,sys,random
from playwright.sync_api import sync_playwright
PORT=8797;R=[]
def rec(g,n,ok,note=''):R.append({'구분':g,'항목':n,'결과':'통과' if ok else '실패','비고':note});print(('통과 ' if ok else '실패 '),g,n,note)
srv=subprocess.Popen(['python3','-m','http.server',str(PORT)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
U=f'http://localhost:{PORT}/'
PAGES=['index','Emergency','Welfare','Transit','All','Culture','Health','Jobs','Centers','Guide','Regions','Ad','Ad2']
TITLE={'Emergency':'급할 때','Welfare':'복지·혜택','Transit':'이동·교통','All':'전체 메뉴'}
NAVLAB=[('홈','index.html'),('급할 때','Emergency.html'),('복지·혜택','Welfare.html'),('이동·교통','Transit.html'),('전체 메뉴','All.html')]
def newpage(b,errs,w=360):
    c=b.new_context(viewport={'width':w,'height':800},is_mobile=True,has_touch=True);pg=c.new_page()
    pg.on('pageerror',lambda e:errs.append('pageerror:'+str(e)[:80]));pg.on('console',lambda m:errs.append('console:'+m.text[:80]) if m.type=='error' and 'ERR_' not in m.text and 'Failed to load resource' not in m.text else None)
    pg.route('**/fonts.googleapis.com/**',lambda r:r.abort());pg.route('**/api.open-meteo.com/**',lambda r:r.abort());return c,pg
try:
  with sync_playwright() as p:
    b=p.chromium.launch();errs=[];c,pg=newpage(b,errs)
    # 1 빠른 연속 누름(더블 탭)
    for lab,href in NAVLAB[1:]:
        pg.goto(U+'index.html');pg.wait_for_selector('#hjFamily');h0=pg.evaluate('history.length')
        try:pg.locator(f'main a[href="{href}"]').first.dblclick()
        except Exception:pass
        t0=time.time()
        while time.time()-t0<6 and not pg.url.endswith(href):time.sleep(0.1)
        time.sleep(0.5)
        while True:
            try:h1=pg.evaluate('history.length');break
            except Exception:time.sleep(0.2)
        rec('중복 누름',f'{lab}: 더블 탭해도 해당 화면 1번만 열림(기록 증가 {h1-h0})',pg.url.endswith(href) and h1-h0<=1)
    # 2 하단 메뉴 40회 무작위 이동
    random.seed(7);pg.goto(U+'index.html');cur='index.html';ok=True;bad=''
    for i in range(40):
        lab,href=random.choice(NAVLAB)
        with pg.expect_navigation():pg.locator('[data-hjnav] a',has_text=lab).first.click()
        if not pg.url.split('#')[0].endswith(href) and not (href=='index.html' and pg.url.endswith('/')):ok=False;bad=f'{i}:{lab}->{pg.url}';break
        if pg.locator('[data-hjnav]').count()!=1:ok=False;bad=f'{i}:하단 메뉴 개수';break
    rec('이동 40회','하단 메뉴 무작위 40번 이동: 항상 맞는 화면·하단 메뉴 1개',ok,bad)
    # 3 하단 「가족 전화」 반복
    pg.goto(U+'Welfare.html')
    for i in range(3):
        with pg.expect_navigation():pg.locator('[data-hjnav] a',has_text='가족 전화').click()
        pg.wait_for_selector('#hjFamily');
        with pg.expect_navigation():pg.go_back()
    rec('가족 전화 이동','3번 반복 이동·뒤로 가기 정상',pg.url.endswith('Welfare.html'),pg.url)
    # 4 뒤로 가기 흐름
    pg.goto(U+'index.html')
    for h in ['Emergency.html','All.html']:
        with pg.expect_navigation():pg.locator(f'[data-hjnav] a[href="{h}"]').first.click()
    with pg.expect_navigation():pg.locator('a[href="Culture.html"]').first.click()
    seq=[]
    for _ in range(3):
        with pg.expect_navigation():pg.go_back()
        seq.append(pg.url.rsplit('/',1)[-1])
    rec('뒤로 가기','전체 메뉴→나들이 뒤로 3번: All→Emergency→index',seq==['All.html','Emergency.html','index.html'],str(seq))
    # 5 「← 처음 화면으로」 전 화면
    bad=[]
    for n in PAGES[1:]:
        pg.goto(U+n+'.html')
        with pg.expect_navigation():pg.locator('a',has_text='처음 화면으로').first.click()
        if not (pg.url.endswith('index.html') or pg.url.endswith('/')):bad.append(n)
    rec('처음 화면으로','12개 화면 모두 첫 화면으로 이동',not bad,str(bad))
    # 6 가족 저장 중복
    pg.goto(U+'index.html');pg.evaluate("localStorage.clear()");pg.reload();pg.wait_for_selector('#hjFamily button')
    pg.click('text=＋ 가족 저장하기');pg.fill('input[aria-label=이름]','큰딸');pg.fill('input[aria-label=전화번호]','010-1234-5678')
    pg.locator('button:has-text("저장하기")').dblclick();pg.wait_for_timeout(200)
    rec('중복 저장','저장하기 더블 탭 → 가족 1명만 저장',pg.locator('a[href^="tel:010"]').count()==1 and pg.evaluate("JSON.parse(localStorage.getItem('hyoja-family')).length")==1)
    pg.click('text=＋ 가족 저장하기');pg.fill('input[aria-label=이름]','큰딸2');pg.fill('input[aria-label=전화번호]','01012345678');pg.click('button:has-text("저장하기")')
    rec('중복 저장','같은 번호 다시 저장 → 「이미 저장된 번호예요」, 1명 유지',pg.locator('text=이미 저장된 번호예요').count()==1 and pg.evaluate("JSON.parse(localStorage.getItem('hyoja-family')).length")==1)
    pg.click('button:has-text("닫기")')
    pg.click('text=저장한 가족 지우기');pg.click('text=저장한 가족 지우기') if pg.locator('text=저장한 가족 지우기').count() else None
    rec('중복 저장','지우기 두 번 눌러도 오류 없음',pg.locator('a[href^="tel:010"]').count()==0)
    # 7 글자 크기 빠른 연타
    for _ in range(3):
        for lab in ['크게','아주 크게','보통']:pg.click(f'#sizeBtns button:has-text("{lab}")',delay=0)
    ov=pg.evaluate('document.documentElement.scrollWidth>document.documentElement.clientWidth+1')
    rec('연타','글자 크기 9번 연타 후 화면 정상(가로 넘침 없음)',not ov)
    # 8 오프라인 전 화면 이동
    pg.goto(U+'index.html');pg.evaluate('navigator.serviceWorker.ready.then(()=>1)');pg.wait_for_timeout(3500)
    for n in PAGES:pg.goto(U+n+'.html');pg.wait_for_timeout(150)
    c.set_offline(True);bad=[]
    for n in PAGES:
        try:
            r=pg.goto(U+n+'.html',timeout=8000);pg.wait_for_timeout(200)
            if not pg.locator('h1').count() or (r and not r.ok and r.status!=0):bad.append(n)
        except Exception as e:bad.append(n+':'+str(e)[:30])
    rec('오프라인','인터넷 끊고 13개 화면 모두 열림',not bad,str(bad))
    try:
        pg.goto(U+'index.html')
        for lab,href in NAVLAB[1:]:
            with pg.expect_navigation(timeout=8000):pg.locator('[data-hjnav] a',has_text=lab).first.click()
            assert pg.locator('h1').count()==1
        rec('오프라인','오프라인에서 하단 메뉴로 이동',True)
    except Exception as e:rec('오프라인','오프라인에서 하단 메뉴로 이동',False,str(e)[:60])
    c.close()
    rec('공통','자바스크립트 오류·콘솔 오류 0건(전 과정)',not errs,';'.join(errs[:3]))
    b.close()
finally:srv.terminate()
ok=sum(1 for r in R if r['결과']=='통과');print(f'\n통과 {ok} / 전체 {len(R)}')
json.dump(R,open('tests/nav-robustness-results.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
sys.exit(0 if ok==len(R) else 1)
