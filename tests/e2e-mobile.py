# 가족 전화·오늘의 안부 + 약국/행정복지센터 노출 차단 모바일 화면 점검 (Chromium 기기 에뮬레이션)
# 실행: python3 tests/e2e-mobile.py   (저장소 루트에서)
import subprocess,time,json,sys,datetime
from playwright.sync_api import sync_playwright
PORT=8791;R=[]
def rec(group,name,ok,note=''):R.append({'구분':group,'항목':name,'결과':'통과' if ok else '실패','비고':note});print(('통과 ' if ok else '실패 '),group,name,note)
srv=subprocess.Popen(['python3','-m','http.server',str(PORT)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
U=f'http://localhost:{PORT}/'
try:
  with sync_playwright() as p:
    b=p.chromium.launch()
    devs=[('Pixel 5(안드로이드 에뮬레이션)',p.devices['Pixel 5']),('iPhone 13(아이폰 화면 에뮬레이션)',p.devices['iPhone 13']),('작은 폰 320px',{'viewport':{'width':320,'height':640},'is_mobile':True,'has_touch':True,'device_scale_factor':2})]
    for dn,dv in devs:
        ctx=b.new_context(**dv);pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto(U+'index.html');pg.wait_for_selector('#hjFamily button')
        g=dn
        rec(g,'첫 화면 열림·안부 카드 보임',pg.locator('text=오늘의 안부').count()>=1)
        rec(g,'자동 알림 없음 문구 표시',pg.locator('text=자동으로 전달되지는 않아요').count()==1)
        pg.click('text=오늘도 잘 지내요');rec(g,'안부 기록 + 「이 휴대폰에」 표시',pg.locator('text=이 휴대폰에 오늘 안부를 기록했어요').count()==1)
        rec(g,'안부 후 「자동 알림 없음」 안내 유지',pg.locator('text=자동으로 알려 주는 기능은 아직 없어요').count()==1)
        pg.click('text=＋ 가족 저장하기')
        pg.fill('input[aria-label=이름]','');pg.fill('input[aria-label=전화번호]','010-1234-5678');pg.click('button:has-text("저장하기")')
        rec(g,'이름 없으면 저장 거부',pg.locator('text=이름을 적어 주세요').count()==1)
        pg.fill('input[aria-label=이름]','큰딸');pg.fill('input[aria-label=전화번호]','12345');pg.click('button:has-text("저장하기")')
        rec(g,'잘못된 번호 거부',pg.locator('text=전화번호를 다시 확인해 주세요').count()==1)
        pg.fill('input[aria-label=전화번호]','010-1234-5678');pg.click('button:has-text("저장하기")')
        rec(g,'전화 링크 tel:01012345678',pg.locator('a[href="tel:01012345678"]').count()==1)
        sms=pg.locator('a[href^="sms:01012345678"]');rec(g,'문자 링크 sms:번호?&body=',sms.count()==1,sms.first.get_attribute('href')[:60] if sms.count() else '')
        for n,ph in [('둘째','010-2222-3333'),('막내','010-4444-5555')]:
            pg.click('text=＋ 가족 저장하기');pg.fill('input[aria-label=이름]',n);pg.fill('input[aria-label=전화번호]',ph);pg.click('button:has-text("저장하기")')
        rec(g,'3명까지 저장',pg.locator('a[href^="tel:010"]').count()==3 and pg.locator('text=＋ 가족 저장하기').count()==0)
        pg.reload();pg.wait_for_selector('#hjFamily button');rec(g,'새로고침 후 유지',pg.locator('a[href^="tel:010"]').count()==3)
        pg.click('text=저장한 가족 지우기');rec(g,'가족 전체 삭제',pg.locator('a[href^="tel:010"]').count()==0)
        rec(g,'삭제 후 안부 문자 버튼 사라짐',pg.locator('a[href^="sms:"]').count()==0)
        # 글씨 크기
        for lab in ['크게','아주 크게']:
            pg.click(f'#sizeBtns button:has-text("{lab}")');pg.wait_for_timeout(200)
            ov=pg.evaluate('document.documentElement.scrollWidth>document.documentElement.clientWidth+1')
            rec(g,f'글자 {lab}: 가로 넘침 없음',not ov)
            pg.click('text=＋ 가족 저장하기');pg.fill('input[aria-label=이름]','큰딸');pg.fill('input[aria-label=전화번호]','010-1234-5678');pg.click('button:has-text("저장하기")')
            box=pg.locator('a[href="tel:01012345678"]').bounding_box();vw=pg.evaluate('document.documentElement.clientWidth')
            rec(g,f'글자 {lab}: 전화 버튼이 화면 안',box and box['x']>=0 and box['x']+box['width']<=vw+1)
            pg.click('text=저장한 가족 지우기')
        pg.click('#sizeBtns button:has-text("보통")')
        rec(g,'자바스크립트 오류 없음',not errs,';'.join(errs)[:80])
        ctx.close()
    # 날짜 변경 (한국시간 자정 경계)
    ctx=b.new_context(**p.devices['Pixel 5'],timezone_id='Asia/Seoul');pg=ctx.new_page()
    pg.clock.install(time=datetime.datetime(2026,11,5,14,59,0,tzinfo=datetime.timezone.utc))   # 한국시간 23:59
    pg.goto(U+'index.html');pg.wait_for_selector('#hjFamily button');pg.click('text=오늘도 잘 지내요')
    rec('날짜','23:59(한국시간) 안부 기록',pg.locator('text=이 휴대폰에 오늘 안부를 기록했어요 (23:59)').count()==1)
    pg.clock.set_fixed_time(datetime.datetime(2026,11,5,15,1,0,tzinfo=datetime.timezone.utc))   # 한국시간 다음날 00:01
    pg.reload();pg.wait_for_selector('#hjFamily button')
    rec('날짜','자정 지나면 기록 초기화',pg.locator('text=이 휴대폰에 오늘 안부를 기록했어요').count()==0 and pg.locator('text=오늘도 잘 지내요').count()>=1)
    ctx.close()
    # 오프라인
    ctx=b.new_context(**p.devices['Pixel 5']);pg=ctx.new_page();pg.goto(U+'index.html');pg.wait_for_selector('#hjFamily button')
    pg.click('text=＋ 가족 저장하기');pg.fill('input[aria-label=이름]','큰딸');pg.fill('input[aria-label=전화번호]','010-1234-5678');pg.click('button:has-text("저장하기")')
    pg.evaluate('navigator.serviceWorker.ready.then(()=>1)');pg.wait_for_timeout(2500);pg.reload();pg.wait_for_timeout(1500)
    ctx.set_offline(True)
    try:
        pg.reload();pg.wait_for_selector('#hjFamily button',timeout=8000)
        rec('오프라인','인터넷 끊고 새로고침해도 화면 열림',True)
        rec('오프라인','오프라인에서 저장한 가족 전화 유지',pg.locator('a[href="tel:01012345678"]').count()==1)
        pg.click('text=오늘도 잘 지내요');rec('오프라인','오프라인에서 안부 기록',pg.locator('text=이 휴대폰에 오늘 안부를 기록했어요').count()==1)
    except Exception as e:rec('오프라인','인터넷 끊고 새로고침해도 화면 열림',False,str(e)[:60])
    ctx.close()
    # 저장소 사용 불가(사생활 보호 모드 비슷)
    ctx=b.new_context(**p.devices['Pixel 5']);ctx.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked')}})");pg=ctx.new_page()
    pg.goto(U+'index.html');pg.wait_for_selector('#hjFamily button')
    pg.click('text=＋ 가족 저장하기');pg.fill('input[aria-label=이름]','큰딸');pg.fill('input[aria-label=전화번호]','010-1234-5678');pg.click('button:has-text("저장하기")')
    rec('저장소 막힘','저장 불가 안내가 뜨고 화면은 계속 작동',pg.locator('text=저장되지 않아요').count()==1)
    ctx.close()
    # 공식 근거 없는 번호 차단
    ctx=b.new_context(**p.devices['iPhone 13']);pg=ctx.new_page();pg.goto(U+'Centers.html');pg.wait_for_timeout(800)
    for nm,num in [('포곡읍','03161935531'),('이동읍','03161935691'),('성복동','03161938777')]:
        rec('노출 차단',f'행정복지센터 {nm} 번호 숨김',pg.locator(f'a[href="tel:{num}"]').count()==0 and pg.locator(f'[data-hj-blocked="{nm}"]').count()==1)
    rec('노출 차단','행정복지센터 나머지 번호 링크 36개 유지',pg.locator('a[href^="tel:0316193"]').count()==36)
    rec('노출 차단','안내 문구 표시',pg.locator('[data-hj-note=centers]').count()==1)
    ctx.close()
    ctx=b.new_context(**p.devices['Pixel 5']);pg=ctx.new_page();pg.goto(U+'Emergency.html');pg.wait_for_selector('button.gu');pg.wait_for_timeout(500)
    bad=0
    for gu in ['처인구','기흥구','수지구']:
        pg.click(f'button.gu[data-gu={gu}]');pg.wait_for_timeout(250)
        if '000-0000' in pg.inner_text('#phList'):bad+=1
    rec('노출 차단','약국 목록에 임시번호(000-0000) 없음',bad==0)
    ctx.close();b.close()
finally:srv.terminate()
ok=sum(1 for r in R if r['결과']=='통과');print(f'\n통과 {ok} / 전체 {len(R)}')
json.dump(R,open('tests/e2e-mobile-results.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
sys.exit(0 if ok==len(R) else 1)
