#!/usr/bin/env python3
"""13화면 × 글씨 크기 3단계 Chromium 모의 검수 (실제 Android/iPhone 아님).
웹 공개 및 정보 게시·통신 없음. 효과/접근성 전체 품질을 대신하지 않음.
"""
import subprocess, time, sys, json
from playwright.sync_api import sync_playwright
PAGES=['index','Emergency','Welfare','Transit','All','Culture','Health','Jobs','Centers','Guide','Regions','Ad','Ad2']
MODES=['보통','크게','아주 크게']
URL='http://127.0.0.1:8798/'
srv=subprocess.Popen([sys.executable,'-m','http.server','8798','--bind','127.0.0.1'],
                     stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1)
checks=[]; errors=[]
try:
    with sync_playwright() as p:
        browser=p.chromium.launch()
        ctx=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
        ctx.route('**/fonts.googleapis.com/**', lambda r:r.abort())
        ctx.route('**/fonts.gstatic.com/**',lambda r:r.abort())
        page=ctx.new_page()
        page.on('pageerror',lambda e:errors.append(str(e)))
        for mode in MODES:
            page.goto(URL+'index.html',wait_until='domcontentloaded')
            page.locator('#sizeBtns').get_by_role('button',name=mode,exact=True).click()
            page.wait_for_timeout(90)
            selected=page.locator('#sizeBtns').get_by_role('button',name=mode,exact=True).get_attribute('aria-pressed')
            checks.append(('글자 버튼 '+mode,selected=='true'))
            for name in PAGES:
                page.goto(URL+name+'.html',wait_until='domcontentloaded')
                page.wait_for_timeout(80)
                result=page.evaluate("""() => {
                    const vw=document.documentElement.clientWidth;
                    const overs=document.documentElement.scrollWidth>vw+1;
                    const visible=e=>{const r=e.getBoundingClientRect();const s=getComputedStyle(e);return r.width>0&&r.height>0&&s.visibility!=='hidden';};
                    const bad=[...document.querySelectorAll('a,button,input,select')]
                        .filter(visible).filter(e=>{const r=e.getBoundingClientRect();return r.width>vw+1||r.left < -2||r.right>vw+2;});
                    return {width:vw,scroll:document.documentElement.scrollWidth,overflow:overs,offscreen:bad.slice(0,2).map(x=>(x.textContent||x.tagName).trim().slice(0,36))};
                }""")
                good=not result['overflow'] and not result['offscreen']
                checks.append((f'{name}/{mode}',good))
                print(('통과 ' if good else '검토필요 ')+f'{name}/{mode} '+json.dumps(result,ensure_ascii=False))
        ctx.close();browser.close()
finally:
    srv.terminate()
    try:srv.wait(timeout=5)
    except Exception:srv.kill()
fail=[name for name,pass_ in checks if not pass_]
print(f"13화면×3글씨 {len(checks)-len(fail)}/{len(checks)} 화면/선택 점검 통과, 예외 {fail[:20]}, JavaScript 오류 {errors[:3]}")
sys.exit(1 if fail or errors else 0)
