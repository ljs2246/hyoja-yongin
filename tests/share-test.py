#!/usr/bin/env python3
"""가족 공유·주소 복사 시험(갤럭시 화면 모의, 실기기 아님). 4가지 상황에서 안내 문구·대체 수단이 나오는지 확인."""
import json,subprocess,sys,time,os
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));PORT=8132
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--directory',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
R=[]
def rec(n,ok):R.append((n,bool(ok)));print(('통과 ' if ok else '실패 ')+n)
def load(pg,init):
    pg.add_init_script(init);pg.goto(f'http://localhost:{PORT}/index.html');pg.wait_for_timeout(700)
with sync_playwright() as p:
    b=p.chromium.launch()
    def page():
        ctx=b.new_context(**p.devices['Galaxy S9+']);return ctx.new_page()
    pg=page();load(pg,"navigator.share=undefined;")
    rec('버튼 문구 "가족에게 공유·주소 복사" 표시',pg.locator('#hj-kakao').count()==1 and '공유·주소 복사' in pg.locator('#hj-kakao').inner_text())
    h=pg.locator('#hj-kakao').bounding_box();rec('버튼 높이 44px 이상',h and h['height']>=44)
    # 1 시스템 공유 있음
    pg=page();load(pg,"window.__sh=[];navigator.share=function(d){window.__sh.push(d);return Promise.resolve()};")
    pg.click('#hj-kakao');pg.wait_for_timeout(300);s=pg.evaluate('window.__sh')
    rec('시스템 공유 창을 열고 제목·주소를 넘김',len(s)==1 and s[0].get('title')=='효자 용인' and s[0].get('url','').endswith('index.html'))
    # 2 공유 실패(취소 아님)
    pg=page();load(pg,"navigator.share=function(){return Promise.reject({name:'NotAllowedError'})};")
    pg.click('#hj-kakao');pg.wait_for_timeout(400)
    rec('공유 실패 시 주소 복사로 자동 전환·안내 문구 표시',pg.locator('#hj-share-msg').is_visible() and ('복사했어요' in pg.locator('#hj-share-msg').inner_text() or 'http' in pg.locator('#hj-share-msg').inner_text()))
    rec('공유 실패 시 문자 보내기 대체 링크 표시',pg.locator('#hj-share-x a[href^="sms:"]').count()==1)
    # 3 사용자가 공유 취소(AbortError)는 오류 문구를 띄우지 않음
    pg=page();load(pg,"navigator.share=function(){return Promise.reject({name:'AbortError'})};")
    pg.click('#hj-kakao');pg.wait_for_timeout(400)
    rec('공유 취소는 오류 문구 없음',not pg.locator('#hj-share-msg').is_visible())
    # 4 시스템 공유 없음 + 클립보드 성공
    pg=page();load(pg,"navigator.share=undefined;window.__ec=0;document.execCommand=function(c){if(c==='copy'){window.__ec++;return true}return false};window.__cp=[];Object.defineProperty(navigator,'clipboard',{value:{writeText:function(t){window.__cp.push(t);return Promise.resolve()}},configurable:true});")
    pg.click('#hj-kakao');pg.wait_for_timeout(400)
    rec('주소 복사 성공 안내',pg.evaluate('window.__cp').__len__()+pg.evaluate('window.__ec')>=1 and '복사했어요' in pg.locator('#hj-share-msg').inner_text())
    # 5 클립보드 거부 → 주소를 화면에 직접 표시
    pg=page();load(pg,"navigator.share=undefined;document.execCommand=function(){return false};Object.defineProperty(navigator,'clipboard',{value:{writeText:function(){return Promise.reject(new Error('x'))}},configurable:true});")
    pg.click('#hj-kakao');pg.wait_for_timeout(400)
    t=pg.locator('#hj-share-msg').inner_text();rec('복사 거부 시 주소를 화면에 직접 표시',('http' in t) and ('복사했어요' not in t))
    # 6 둘 다 없음
    pg=page();load(pg,"navigator.share=undefined;document.execCommand=function(){return false};Object.defineProperty(navigator,'clipboard',{value:undefined,configurable:true});")
    pg.click('#hj-kakao');pg.wait_for_timeout(400)
    rec('공유·복사 모두 없으면 주소를 보여 주며 안내',pg.locator('#hj-share-msg').is_visible() and 'http' in pg.locator('#hj-share-msg').inner_text())
    # 7 안드로이드 크롬 열기 링크 안전성(주소가 우리 사이트 주소만 포함)
    pg=page();load(pg,"navigator.share=undefined;")
    pg.click('#hj-kakao');pg.wait_for_timeout(300)
    hrefs=pg.eval_on_selector_all('#hj-share-x a','e=>e.map(x=>x.href)')
    rec('보내기 링크에 개인정보 없음(문자·크롬 열기만)',all(h.startswith(('sms:','intent://')) for h in hrefs) and len(hrefs)>=1)
    b.close()
srv.terminate()
f=sum(1 for _,o in R if not o)
json.dump({'통과':len(R)-f,'실패':f,'항목':[{'이름':n,'결과':'통과' if o else '실패'} for n,o in R],'비고':'갤럭시 화면 모의, 실기기 아님'},open(os.path.join(ROOT,'tests/share-results.json'),'w'),ensure_ascii=False,indent=1)
print(f'공유 시험: 통과 {len(R)-f} / 실패 {f}');sys.exit(1 if f else 0)
