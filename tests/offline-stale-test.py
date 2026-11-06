#!/usr/bin/env python3
"""오프라인 옛 저장본 안전 시험(모의 브라우저 Chromium, 실기기 아님).
임시 폴더에 앱을 복사해 자료 날짜만 바꾼 뒤, 서비스워커가 저장한 자료를 인터넷 없이 열었을 때
(A) 오래된 자료면 경고가 뜨고 약국 전화 버튼이 0개인지, (B) 최근 자료면 경고가 뜨지 않는지 확인한다. 실제 자료 파일은 바꾸지 않는다."""
import json,shutil,subprocess,sys,tempfile,time,datetime,os
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));R=[]
def rec(n,ok,note=''):R.append({'항목':n,'결과':'통과' if ok else '실패','비고':note});print('통과' if ok else '실패',n,note)
def serve(stamp,port):
    d=tempfile.mkdtemp()
    shutil.copytree(ROOT,d+'/app',ignore=shutil.ignore_patterns('.git','node_modules','docs','tests'))
    for f in('pharmacy','emergency'):
        p=f'{d}/app/data/{f}.json';j=json.load(open(p));j['확인한 때']=stamp;json.dump(j,open(p,'w'),ensure_ascii=False)
    s=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--directory',d+'/app'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1);return s,d
def run(b,p,stamp,port,expect_alert,label):
    s,d=serve(stamp,port)
    try:
        ctx=b.new_context(**p.devices['Pixel 5']);pg=ctx.new_page();U=f'http://localhost:{port}/'
        pg.goto(U+'Emergency.html');pg.wait_for_selector('button.gu');pg.evaluate('navigator.serviceWorker.ready.then(()=>1)');pg.wait_for_timeout(2500)
        pg.reload();pg.wait_for_timeout(1500);ctx.set_offline(True)
        pg.reload();pg.wait_for_selector('button.gu',timeout=10000);pg.click('button.gu[data-gu=기흥구]');pg.wait_for_timeout(600)
        alert=pg.locator('[role=alert]:has-text("자료 확인일이 오래됐어요")').count()
        tel=pg.locator('#phList a[href^="tel:"]').count();items=pg.locator('#phList > *').count()
        rec(f'{label}: 인터넷 끊고 열어도 약국 목록 표시',items>0,f'항목 {items}')
        rec(f'{label}: 오래된 자료 경고 '+('표시' if expect_alert else '없음(거짓 경고 없음)'),(alert==1) if expect_alert else (alert==0),f'경고 {alert}개')
        rec(f'{label}: 약국 전화 버튼 0개',tel==0,f'tel {tel}개')
        ctx.close()
    finally:s.terminate();shutil.rmtree(d,ignore_errors=True)
today=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
with sync_playwright() as p:
    b=p.chromium.launch()
    run(b,p,'2026-10-01 00:00',8123,True,'A 옛 저장본(30일 전)')
    run(b,p,(today-datetime.timedelta(hours=3)).strftime('%Y-%m-%d %H:%M'),8124,False,'B 최근 저장본(3시간 전)')
    b.close()
f=sum(r['결과']=='실패' for r in R);print(f'오프라인 옛 저장본 시험: 통과 {len(R)-f} / 실패 {f} (모의 브라우저, 실기기 아님)')
json.dump(R,open(os.path.join(ROOT,'tests/offline-stale-results.json'),'w'),ensure_ascii=False,indent=1);sys.exit(1 if f else 0)
