# 효자 새 방문·개인정보 삭제 모의 브라우저 시험. 실제 폰·환자정보 시험 아님.
import pathlib, sys
from playwright.sync_api import sync_playwright

index=(pathlib.Path(__file__).parent/"index.html").resolve().as_uri()
checks=[]
def check(name,cond):
    checks.append((name,bool(cond)))
    print(("통과: " if cond else "실패: ")+name)

with sync_playwright() as p:
    browser=p.chromium.launch()
    page=browser.new_page(viewport={"width":390,"height":844})
    errors=[]; network=[]
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("request", lambda r: network.append(r.url))
    page.goto(index)
    check("새 방문 버튼이 보임",page.locator("#newVisit").is_visible())
    check("전체 방문기록 삭제 버튼이 보임",page.locator("#clearVisit").is_visible())
    check("정보 삭제/공용 휴대폰 안내", "공용 휴대폰" in page.locator("#app").inner_text())
    page.evaluate("""() => {
        localStorage.setItem('hj_visit_v1', JSON.stringify({
            ticket: 'A-123',photo:'data:image/jpeg;base64,FAKE',ticketAt:100,dueAt:123,
            visitDate:'2026-10-31',visitTime:'09:00',hosp:'가상 의원',hospTel:'0310000000',home:'가상 집'
        }));
        localStorage.setItem('hyoja-family',JSON.stringify([{name:'가족',phone:'010-1234-5678'}]));
    }""")
    page.reload()
    check("이전 번호를 홈에서 확인", "A-123" in page.locator("#app").inner_text())
    page.on("dialog",lambda d: d.accept())
    page.locator("#newVisit").click()
    data=page.evaluate("JSON.parse(localStorage.getItem('hj_visit_v1'))")
    check("새 방문: 접수번호·사진 삭제",not any(k in data for k in ("ticket","photo","ticketAt")))
    check("새 방문: 시간 알림·예약 메모 삭제",not any(k in data for k in ("dueAt","visitDate","visitTime")))
    check("새 방문: 병원 이름·연락처 유지",data.get("hosp")=="가상 의원" and data.get("hospTel")=="0310000000")
    check("새 방문: 사용자에게 결과 안내","지웠어요" in page.locator("#privacyMsg").inner_text())
    page.locator("#clearVisit").click()
    check("전체 방문기록 삭제: 로컬 키 제거",page.evaluate("localStorage.getItem('hj_visit_v1')===null"))
    check("전체 방문기록 삭제: 가족 연락처 보존",page.evaluate("JSON.parse(localStorage.getItem('hyoja-family'))[0].name")== "가족")
    check("삭제 후 이전 번호 표시 안 함","A-123" not in page.locator("#app").inner_text())
    check("누를 곳 48px 이상",page.evaluate("""[...document.querySelectorAll('button,a.btn')].filter(e=>e.offsetParent!==null).every(e=>e.getBoundingClientRect().height>=48)"""))
    check("390px 화면에서 가로 스크롤 없음",page.evaluate("document.documentElement.scrollWidth<=window.innerWidth"))
    check("외부 서버 요청 없음",not any(not (x.startswith("file:") or x.startswith("data:")) for x in network))
    check("브라우저 자바스크립트 오류 없음",not errors)
    browser.close()

bad=[name for name,ok in checks if not ok]
print(f"\n{len(checks)-len(bad)}/{len(checks)} 통과. 실패: {bad}")
sys.exit(1 if bad else 0)
