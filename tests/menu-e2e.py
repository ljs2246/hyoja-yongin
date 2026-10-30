# 13개 화면 메뉴 이름·이동 흐름 통일 + 첫 화면 핵심 4개 + 안부·위치 기능 부재 점검 (Chromium 모의 기기)
# 실행: python3 tests/menu-e2e.py   (저장소 루트에서)
import subprocess,time,json,sys
from playwright.sync_api import sync_playwright
PORT=8793;R=[]
def rec(g,n,ok,note=''):R.append({'구분':g,'항목':n,'결과':'통과' if ok else '실패','비고':note});print(('통과 ' if ok else '실패 '),g,n,note)
srv=subprocess.Popen(['python3','-m','http.server',str(PORT)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
U=f'http://localhost:{PORT}/'
PAGES=['index','Emergency','Welfare','Transit','All','Culture','Health','Jobs','Centers','Guide','Regions','Ad','Ad2']
NAV=['홈','가족 전화','급할 때','복지·혜택','이동·교통','전체 메뉴']
HREF=['index.html','index.html#hjFamily','Emergency.html','Welfare.html','Transit.html','All.html']
H1={'Emergency':'급할 때','Welfare':'복지·혜택','Transit':'이동·교통','All':'전체 메뉴','Culture':'문화·나들이','Health':'건강교실','Jobs':'일자리','Centers':'우리 동네 행정복지센터','Guide':'이 앱 쓰는 법'}
CUR={'index':'홈','Emergency':'급할 때','Welfare':'복지·혜택','Transit':'이동·교통','All':'전체 메뉴'}
try:
  with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':360,'height':800},is_mobile=True,has_touch=True);pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/fonts.googleapis.com/**',lambda r:r.abort());pg.route('**/api.open-meteo.com/**',lambda r:r.abort())
    for name in PAGES:
        pg.goto(U+name+'.html');pg.wait_for_timeout(300)
        navs=pg.evaluate("[...document.querySelectorAll('[data-hjnav]')].map(n=>[...n.querySelectorAll('a')].map(a=>[a.textContent.trim(),a.getAttribute('href'),a.getAttribute('aria-current')]))")
        ok=len(navs)==1 and [x[0] for x in navs[0]]==NAV and [x[1] for x in navs[0]]==HREF
        rec('하단 메뉴',f'{name}: 메뉴 6개 이름·순서·이동 대상 동일',ok,str(navs)[:80] if not ok else '')
        cur=[x[0] for x in navs[0] if x[2]] if navs else []
        want=CUR.get(name,'전체 메뉴')
        rec('하단 메뉴',f'{name}: 현재 위치 표시 1곳({want})',cur==[want],str(cur))
        if name!='index':
            back=pg.evaluate("[...document.querySelectorAll('a')].filter(a=>/^[←‹]/.test(a.textContent.trim())).map(a=>[a.textContent.trim(),a.getAttribute('href')])")
            rec('뒤로 가기',f'{name}: 「← 처음 화면으로」 → index.html',back==[['← 처음 화면으로','index.html']],str(back))
        if name in H1:
            h=pg.evaluate("document.querySelector('h1').innerText.trim()")
            rec('이름 통일',f'{name}: 화면 제목 = 「{H1[name]}」',h==H1[name],h)
            rec('이름 통일',f'{name}: 브라우저 제목에 「{H1[name]}」 포함',H1[name] in pg.title(),pg.title())
        body=pg.inner_text('body')
        rec('제외 기능',f'{name}: 오늘의 안부 기록·위치 공유·추적·약 복용 알림 문구 없음',not any(x in body for x in ['오늘의 안부','오늘도 잘 지내요','위치 공유','위치 추적','약 복용 알림','복용 알림']))
    # 첫 화면
    pg.goto(U+'index.html');pg.wait_for_selector('#hjFamily');pg.wait_for_timeout(300)
    core=pg.evaluate("""()=>{const m=document.querySelector('.primary-menu');return {title:document.getElementById('core4-title')&&document.getElementById('core4-title').innerText,
      famTop:document.getElementById('hjFamily').getBoundingClientRect().top+scrollY, emTop:document.querySelector('a[href="Emergency.html"]').getBoundingClientRect().top+scrollY,
      menu:[...m.querySelectorAll('a')].map(a=>a.getAttribute('href')), all:document.querySelector('a.hj-all-menu')&&document.querySelector('a.hj-all-menu').getAttribute('href'),
      mainLinks:[...document.querySelectorAll('main a')].map(a=>a.getAttribute('href')).filter(h=>/^(Culture|Health|Jobs|Centers|Guide)\\.html/.test(h||''))}}""")
    rec('첫 화면','큰 제목 「꼭 필요한 4가지」',core['title']=='꼭 필요한 4가지')
    rec('첫 화면','핵심 4개 = 가족 전화(카드)·급할 때·복지·혜택·이동·교통',core['menu']==['Welfare.html','Transit.html'] and core['famTop']<core['emTop'])
    rec('첫 화면','나머지 메뉴는 「전체 메뉴」 한 곳으로(나들이·건강교실·일자리 바로가기 없음 — 새소식 영역 제외)',core['all']=='All.html' and pg.evaluate("document.querySelectorAll('.primary-menu a').length")==2)
    rec('첫 화면','핵심 4개가 모두 3화면 분량(2400px) 안',core['emTop']<2400)
    # 이동 흐름
    for lab,href,h in [('급할 때','Emergency.html','급할 때'),('복지·혜택','Welfare.html','복지·혜택'),('이동·교통','Transit.html','이동·교통'),('전체 메뉴','All.html','전체 메뉴')]:
        pg.goto(U+'index.html');pg.wait_for_selector('#hjFamily');
        with pg.expect_navigation():pg.locator(f'main a[href="{href}"]').first.click()
        rec('이동 흐름',f'첫 화면 → {lab} 화면',pg.evaluate("document.querySelector('h1').innerText.trim()")==h)
        
        with pg.expect_navigation():pg.locator('[data-hjnav] a',has_text='홈').first.click()
        rec('이동 흐름',f'{lab} → 하단 「홈」 → 첫 화면',pg.url.endswith('index.html') or pg.url.endswith('/'))
    pg.goto(U+'Welfare.html');pg.locator('[data-hjnav] a',has_text='가족 전화').click();pg.wait_for_selector('#hjFamily');pg.wait_for_timeout(300)
    rec('이동 흐름','하단 「가족 전화」 → 첫 화면의 가족 전화 카드',pg.url.endswith('index.html#hjFamily') and pg.evaluate("(()=>{const r=document.getElementById('hjFamily').getBoundingClientRect();return r.top<700&&r.bottom>0})()"))
    # 전체 메뉴 구성
    pg.goto(U+'All.html');hs=pg.evaluate("[...document.querySelectorAll('h2')].map(h=>h.innerText.trim())")
    links=pg.evaluate("[...document.querySelectorAll('main a, .hj-content a')].map(a=>a.getAttribute('href'))")
    rec('전체 메뉴','3개 묶음(꼭 필요한 4가지·더 알아보기·처음 쓰시는 분·설정)',hs==['꼭 필요한 4가지','더 알아보기','처음 쓰시는 분 · 설정'],str(hs))
    rec('전체 메뉴','나머지 메뉴 전부 포함(나들이·건강교실·일자리·행정복지센터·쓰는 법·지역)',all(x in links for x in ['Culture.html','Health.html','Jobs.html','Centers.html','Guide.html','Regions.html','index.html#hjFamily','Emergency.html','Welfare.html','Transit.html']))
    # 크기·넘침
    for w in (320,360,480):
        c2=b.new_context(viewport={'width':w,'height':800},is_mobile=True,has_touch=True);q=c2.new_page();q.route('**/fonts.googleapis.com/**',lambda r:r.abort());q.route('**/api.open-meteo.com/**',lambda r:r.abort())
        for name in ['index','All','Welfare','Regions','Ad']:
            q.goto(U+name+'.html');q.wait_for_timeout(250)
            for lab in ['보통','크게','아주 크게']:
                if q.locator(f'#sizeBtns button:has-text("{lab}")').count():
                    q.click(f'#sizeBtns button:has-text("{lab}")');q.wait_for_timeout(120)
                ov=q.evaluate('document.documentElement.scrollWidth>document.documentElement.clientWidth+1')
                navbad=q.evaluate("(()=>{const n=document.querySelector('[data-hjnav]');if(!n)return 'nonav';const vw=document.documentElement.clientWidth;return [...n.querySelectorAll('a')].some(a=>{const r=a.getBoundingClientRect();return r.height<44||r.right>vw+1||r.left<-1||a.scrollWidth>a.clientWidth+1})})()")
                rec('화면 맞춤',f'{w}px {name} 글자 {lab}: 가로 넘침 없음·하단 메뉴 잘림 없음·높이 44px 이상',(not ov) and navbad is False,f'overflow={ov} nav={navbad}')
                if lab=='아주 크게' and q.locator('#sizeBtns button:has-text("보통")').count():q.click('#sizeBtns button:has-text("보통")')
        c2.close()
    rec('공통','자바스크립트 오류 없음',not errs,';'.join(errs)[:80])
    ctx.close();b.close()
finally:srv.terminate()
ok=sum(1 for r in R if r['결과']=='통과');print(f'\n통과 {ok} / 전체 {len(R)}')
json.dump(R,open('tests/menu-e2e-results.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
sys.exit(0 if ok==len(R) else 1)
