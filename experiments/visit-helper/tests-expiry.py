# 자동 만료(12시간)·저장 시각 표시 모의 브라우저 시험 — 실기기 시험 아님
import sys, pathlib, json
from playwright.sync_api import sync_playwright
root=pathlib.Path(__file__).parent.resolve(); URL=(root/"index.html").as_uri()
res=[]; errs=[]
def ok(n,c): res.append((n,bool(c))); print(("통과 " if c else "실패 ")+n)
H=3600000
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":390,"height":844}); pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto(URL)
    def seed(age_h, with_photo=True):
        pg.evaluate("""([age,wp])=>{const t=Date.now()-age;const o={ticket:'A-023',ticketAt:t,dueAt:Date.now()+600000,hosp:'가상의원',hospTel:'031-123-4567',home:'가상 아파트',visitDate:'2026-11-05'};
          if(wp){o.photo='data:image/jpeg;base64,AAAA';o.photoAt=t;} localStorage.setItem('hj_visit_v1',JSON.stringify(o));
          localStorage.setItem('hyoja-family',JSON.stringify([{name:'큰딸',phone:'010-1234-5678'}]));}""",[age_h*H,with_photo])
        pg.reload()
    seed(13)
    o=pg.evaluate("JSON.parse(localStorage.getItem('hj_visit_v1')||'{}')")
    ok("13시간 지난 접수번호·사진·알림 자동 삭제", not any(k in o for k in ["ticket","ticketAt","photo","photoAt","dueAt"]))
    ok("자동 삭제 뒤 병원 이름·전화 유지", o.get("hosp")=="가상의원" and o.get("hospTel")=="031-123-4567")
    ok("가족 연락처는 건드리지 않음", pg.evaluate("JSON.parse(localStorage.getItem('hyoja-family')).length")==1)
    seed(1)
    o=pg.evaluate("JSON.parse(localStorage.getItem('hj_visit_v1'))")
    ok("1시간 지난 정보는 유지", o.get("ticket")=="A-023" and o.get("photo"))
    # 이미 열린 화면에서 시간이 지나고 다시 초점을 얻을 때도 삭제해야 한다.
    seed(1)
    pg.evaluate("""() => {window.__clockOriginal=Date.now;Date.now=()=>window.__clockOriginal()+13*3600000;window.dispatchEvent(new Event('focus'));}""")
    ok("열린 화면에서 12시간 경과·포커스 복귀 시 자동 삭제", pg.evaluate("!JSON.parse(localStorage.getItem('hj_visit_v1')).ticket"))
    pg.evaluate("Date.now=window.__clockOriginal;delete window.__clockOriginal")
    seed(11.9)
    ok("11시간 54분 지난 정보는 유지(경계)", pg.evaluate("JSON.parse(localStorage.getItem('hj_visit_v1')).ticket")=="A-023")
    seed(12.1)
    ok("12시간 6분 지난 정보는 삭제(경계)", pg.evaluate("!JSON.parse(localStorage.getItem('hj_visit_v1')).ticket"))
    ok("홈에 12시간 자동 삭제 안내", "12시간이 지나면" in pg.inner_text("#app"))
    pg.goto(URL+"#/ticket"); pg.fill("#tn","B-7")
    ok("접수 화면에 저장 시각·자동 삭제 안내", "저장한 시각" in pg.inner_text("#show") and "12시간 뒤 자동 삭제" in pg.inner_text("#show"))
    # 사진 없이 번호만 있어도 만료
    seed(13,False)
    ok("사진 없이 번호만 있어도 만료", pg.evaluate("!JSON.parse(localStorage.getItem('hj_visit_v1')).ticket"))
    # 저장소 사용 불가 환경에서도 오류 없음
    pg.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked')}})")
    pg.goto(URL); ok("저장소가 막혀도 화면이 열림", "병원 방문 도우미" in pg.inner_text("#app"))
    b.close()
ok("자바스크립트 오류 0건", not errs)
f=[n for n,c in res if not c]; print(f"\n{len(res)-len(f)}/{len(res)} 통과", errs); sys.exit(1 if f else 0)
