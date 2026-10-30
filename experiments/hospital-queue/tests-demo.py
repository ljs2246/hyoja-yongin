# 시험 견본(demo.html) 모의 브라우저 시험 — 실기기 시험이 아님
import sys, pathlib
from playwright.sync_api import sync_playwright
root = pathlib.Path(__file__).parent.resolve()
errs=[]; res=[]
def ok(name,cond):
    res.append((name,bool(cond))); print(("통과 " if cond else "실패 ")+name)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":390,"height":844})
    pg.on("pageerror",lambda e:errs.append(str(e))); pg.on("dialog",lambda d:d.accept())
    pg.goto((root/"demo.html").as_uri())
    ok("광고 요소 없음", pg.locator("iframe,ins,[class*=ad-]").count()==0)
    # 직원: 현재 호출 번호 + A-023 인원 확정
    pg.fill("#cc","A-020"); pg.click("#ccBtn")
    pg.locator("button[aria-label='A-023 수정']").click()
    ok("번호 차이는 참고값(확정 아님)으로 표시", "확정 아님" in pg.inner_text("#sugg") and "2명" in pg.inner_text("#sugg"))
    pg.fill("#ahead","4"); pg.click("#apply")
    pg.click("#tabP"); pg.select_option("#mine",label="A-023")
    ok("환자 화면에 직원이 확정한 4명 표시(번호 차이 2명이 아님)", pg.inner_text("#pAhead")=="4")
    ok("현재 호출 번호는 참고로만 표시", "A-020" in pg.inner_text("#pCall"))
    ok("검증 안 된 예상 대기시간 숨김", not pg.locator("#pEta").is_visible())
    ok("마지막 갱신 시각 표시", "초 전" in pg.inner_text("#pAge"))
    fs=pg.evaluate("parseFloat(getComputedStyle(document.getElementById('pAhead')).fontSize)")
    ok("숫자 글자 크기 48px 이상", fs>=48)
    # 접수 안 한 다른 환자는 정보 없음
    pg.select_option("#mine",label="A-024")
    ok("정보 없는 접수는 숫자 대신 안내", pg.inner_text("#pAhead")=="-" and "현장 호출" in pg.inner_text("#pAlert"))
    # 갱신 지연: 시계 3분 앞으로
    pg.select_option("#mine",label="A-023")
    pg.evaluate("(()=>{const r=Date.now;Date.now=()=>r()+180000;})()")
    pg.wait_for_timeout(1300)
    ok("3분 갱신 중단 시 숫자 숨김+지연 안내", pg.inner_text("#pAhead")=="-" and "지연" in pg.inner_text("#pAlert"))
    pg.reload()
    # 호출 → 취소 후 호출 거부
    pg.locator("button[aria-label='A-021 수정']").click(); pg.click("#cancelB")
    pg.click("#callB")
    ok("취소 뒤 호출은 거부 메시지", "terminal_state" in pg.inner_text("#edMsg"))
    pg.click("#tabP"); pg.select_option("#mine",label="A-021")
    ok("취소 상태 안내", "취소" in pg.inner_text("#pAlert"))
    # 지연 → 숫자 숨김
    pg.click("#tabS"); pg.locator("button[aria-label='A-022 수정']").click()
    pg.fill("#ahead","3"); pg.click("#apply"); pg.click("#delayB")
    pg.click("#tabP"); pg.select_option("#mine",label="A-022")
    ok("지연 상태에서 숫자 숨김", pg.inner_text("#pAhead")=="-" and "지연" in pg.inner_text("#pAlert"))
    # 입력 검증
    pg.click("#tabS"); pg.locator("button[aria-label='A-025 수정']").click()
    pg.fill("#ahead","-3"); pg.click("#apply")
    ok("잘못된 인원 입력 거부", "숫자" in pg.inner_text("#edMsg"))
    ok("버튼 높이 48px 이상", pg.evaluate("[...document.querySelectorAll('button')].filter(b=>b.offsetParent).every(b=>b.getBoundingClientRect().height>=48)"))
    ok("가로 스크롤 없음", pg.evaluate("document.documentElement.scrollWidth<=window.innerWidth"))
    b.close()
ok("자바스크립트 오류 0건", not errs)
bad=[n for n,c in res if not c]
print(f"\n{len(res)-len(bad)}/{len(res)} 통과", errs)
sys.exit(1 if bad else 0)
