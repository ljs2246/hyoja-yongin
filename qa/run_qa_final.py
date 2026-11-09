#!/usr/bin/env python3
"""효자 2차 디자인 최종 보완 검수: (A) 첫 화면에 '급할 때' 보임 · (B) 오프라인(서비스워커) · (C) 앱을 완전히 닫았다 켠 뒤 지역·가족 유지(영구 저장소 재실행) · (D) 공유 동작.
결과: PASS/FAIL/WARN/DEVICE. 실패가 있으면 종료코드 1. 사용: python3 qa/run_qa_final.py [--out 폴더]"""
import argparse, functools, http.server, io, json, os, re, shutil, socketserver, sys, tempfile, threading
from playwright.sync_api import sync_playwright
ap = argparse.ArgumentParser(); ap.add_argument('--out', default='qa-report-final'); ap.add_argument('--root', default=None); a = ap.parse_args()
ROOT = a.root or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.abspath(a.out); os.makedirs(OUT, exist_ok=True)
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT); H.log_message = lambda *x: None
srv = socketserver.TCPServer(('127.0.0.1', 0), H); U = f'http://127.0.0.1:{srv.server_address[1]}/'; threading.Thread(target=srv.serve_forever, daemon=True).start()
R = []
def rec(g, n, s, d=''):
    R.append(dict(group=g, name=n, status=s, detail=d)); print(f"[{ {'PASS':'통과','FAIL':'실패','WARN':'경고','DEVICE':'실기기 확인 필요'}[s]}] {g} · {n}" + (f' · {d}' if d else ''))
PAGES = ['index', 'Emergency', 'Health', 'Welfare', 'Transit', 'Culture', 'Jobs', 'Guide', 'All', 'Centers', 'Regions', 'Ad', 'Ad2']
def route(pg): pg.route(re.compile(r'.*open-meteo.*'), lambda r: r.abort())
def jpeg():
    from PIL import Image; im = Image.new('RGB', (300, 220), (200, 120, 90)); b = io.BytesIO(); im.save(b, 'JPEG'); return b.getvalue()
with sync_playwright() as p:
    b = p.chromium.launch()
    # A. 첫 화면
    g = 'A 첫 화면 급할 때'
    bad = []; n = 0
    for w, h in ((320, 640), (360, 800), (390, 844), (412, 915)):
        for z in ('normal', 'large', 'xl'):
            c = b.new_context(viewport={'width': w, 'height': h}, is_mobile=True, has_touch=True); pg = c.new_page(); route(pg)
            pg.goto(U + 'index.html'); pg.wait_for_timeout(1000)
            if z != 'normal':
                pg.evaluate("(i)=>{const x=document.querySelectorAll('#sizeBtns button');x[i]&&x[i].click()}", 1 if z == 'large' else 2); pg.wait_for_timeout(700)
            r = pg.evaluate("(()=>{const u=document.querySelector('.hj-urgent').getBoundingClientRect(),nv=document.querySelector('.home-nav').getBoundingClientRect(),H=innerHeight;return {top:Math.round(u.top),bottom:Math.round(u.bottom),nav:Math.round(nv.top),ov:document.documentElement.scrollWidth>document.documentElement.clientWidth,h:H}})()")
            n += 1
            ok = r['top'] >= 0 and r['bottom'] <= r['nav'] and not r['ov']
            if not ok: bad.append((w, h, z, r))
            if w == 390 and z == 'normal': pg.screenshot(path=f'{OUT}/A_home_390.png')
            c.close()
    rec(g, f'4폭 × 글자 3단계({n}조건): 급할 때 버튼이 하단 메뉴 위 첫 화면에 보이고 좌우 넘침 없음', 'PASS' if not bad else 'FAIL', str(bad)[:300])
    # B. 오프라인
    g = 'B 오프라인'
    c = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True); pg = c.new_page(); route(pg)
    pg.goto(U + 'index.html'); pg.wait_for_timeout(800)
    sw = pg.evaluate("navigator.serviceWorker?navigator.serviceWorker.ready.then(r=>!!r.active):false")
    rec(g, '서비스워커 등록·활성', 'PASS' if sw else 'FAIL')
    for pn in PAGES[1:]: pg.goto(U + pn + '.html'); pg.wait_for_timeout(250)   # 한 번씩 열어 저장
    pg.goto(U + 'index.html'); pg.wait_for_timeout(1500)
    keys = pg.evaluate("caches.keys().then(async k=>{const o={};for(const n of k){o[n]=(await (await caches.open(n)).keys()).length}return o})")
    rec(g, '화면·스크립트가 기기에 저장됨(캐시)', 'PASS' if keys and max(keys.values()) >= 30 else 'FAIL', str(keys))
    c.set_offline(True); fails = []; nosay = []
    for pn in PAGES:
        try:
            pg.goto(U + pn + '.html', wait_until='domcontentloaded', timeout=8000); pg.wait_for_timeout(700)
            t = pg.evaluate("document.body.innerText.length"); h1 = pg.evaluate("!!document.querySelector('h1,.hj-urgent')")
            if t < 80 or not h1: fails.append(pn)
            if pn != 'Review' and pg.evaluate("document.querySelectorAll('.hj-say2,.hj-say').length") == 0 and pn not in ('Ad', 'Ad2', 'Guide'): nosay.append(pn)
        except Exception as e: fails.append(pn + ':' + str(e)[:40])
    rec(g, '인터넷 끊김 상태에서 13개 화면이 열림', 'PASS' if not fails else 'FAIL', f'열리지 않음: {fails}')
    rec(g, '인터넷 끊김 상태에서도 🔊 버튼이 보임', 'PASS' if not nosay else 'FAIL', str(nosay))
    pg.goto(U + 'Emergency.html'); pg.wait_for_timeout(900)
    rec(g, '끊김 상태 응급 화면에 전화 목록이 보임', 'PASS' if pg.evaluate("document.querySelectorAll('a[href^=\"tel:\"]').length") >= 3 else 'FAIL')
    c.set_offline(False); pg.goto(U + 'index.html'); pg.wait_for_timeout(1000)
    rec(g, '인터넷이 다시 연결되면 정상 화면', 'PASS' if pg.evaluate("!!document.querySelector('.hj-urgent')") else 'FAIL')
    rec(g, '실제 갤럭시 데이터·와이파이를 끄고 켜는 상황', 'DEVICE', '여기서는 localhost에서 연결 끊김을 흉내 냈어요. 운영 주소에서의 실제 동작은 별도 시험 필요(시험 주소는 서비스워커 불가)')
    c.close()
    # C. 앱 완전 종료 후 재실행 (영구 저장소를 닫았다가 다시 열기)
    g = 'C 완전 종료 후 유지'
    ud = tempfile.mkdtemp(prefix='hjqa_')
    def open_ctx():
        c = p.chromium.launch_persistent_context(ud, viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True); pg = c.pages[0] if c.pages else c.new_page(); route(pg); return c, pg
    c, pg = open_ctx()
    pg.goto(U + 'Regions.html'); pg.wait_for_selector('#region-mine-select'); pg.wait_for_timeout(500)
    opts = pg.evaluate("[...document.querySelectorAll('#region-mine-select option')].map(o=>[o.value,o.textContent])"); pick = next((o for o in opts if '기흥' in o[1]), opts[1])
    pg.select_option('#region-mine-select', pick[0]); pg.wait_for_timeout(400)
    pg.goto(U + 'index.html'); pg.wait_for_timeout(1000)
    pg.locator('#hjFamily button:has-text("가족 저장하기")').first.click()
    pg.fill('#hjFamily input[aria-label*="이름"]', '큰딸'); pg.fill('#hjFamily input[aria-label*="전화"]', '010-1234-5678')
    pg.set_input_files('#hjFamily input[type=file]', {'name': 'p.jpg', 'mimeType': 'image/jpeg', 'buffer': jpeg()}); pg.wait_for_timeout(700)
    pg.locator('#hjFamily button:has-text("저장하기")').last.click(); pg.wait_for_timeout(500)
    c.close()   # 브라우저를 완전히 닫음
    c, pg = open_ctx(); pg.goto(U + 'index.html'); pg.wait_for_timeout(1200)
    st = pg.evaluate("localStorage.getItem('hyoja-family')") or ''
    rec(g, '브라우저를 완전히 닫았다 다시 열어도 가족 이름·번호 유지', 'PASS' if '큰딸' in st and '01012345678' in st else 'FAIL')
    rec(g, '브라우저를 완전히 닫았다 다시 열어도 가족 사진 유지', 'PASS' if 'data:image/jpeg;base64,' in st else 'FAIL', f'{len(st)}바이트')
    rec(g, '다시 열어도 가족 전화 버튼 표시', 'PASS' if pg.locator('#hjFamily a[href^="tel:"]').count() == 1 else 'FAIL')
    txt = pg.evaluate('document.body.innerText')
    rec(g, '브라우저를 완전히 닫았다 다시 열어도 저장한 지역 유지', 'PASS' if pick[1] in txt else 'FAIL', f'기대={pick[1]}')
    c.close(); shutil.rmtree(ud, ignore_errors=True)
    rec(g, '갤럭시 Chrome 최근 앱에서 밀어서 종료 후 재실행', 'DEVICE', '여기서는 저장소를 닫았다 여는 방식으로 확인. 실제 기기 종료는 갤럭시에서 확인')
    # D. 공유
    g = 'D 가족에게 보내기'
    c = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True); pg = c.new_page(); route(pg)
    c.add_init_script("window.__sh=[];Object.defineProperty(navigator,'share',{value:d=>{window.__sh.push(d);return Promise.resolve();},configurable:true});window.__cb=[];Object.defineProperty(navigator,'clipboard',{value:{writeText:t=>{window.__cb.push(t);return Promise.resolve();}},configurable:true});")
    pg.goto(U + 'index.html'); pg.wait_for_timeout(1000)
    pg.locator('#hj-kakao').first.scroll_into_view_if_needed(); pg.locator('#hj-kakao').first.click(); pg.wait_for_timeout(500)
    sh = pg.evaluate('window.__sh'); cb = pg.evaluate('window.__cb')
    ok = bool(sh) and all(k in ('title', 'text', 'url') for k in sh[0]) and '010' not in json.dumps(sh, ensure_ascii=False)
    rec(g, '공유 창(휴대폰 공유 기능) 호출 시 화면 이름·주소만 전달', 'PASS' if ok else ('WARN' if cb else 'FAIL'), json.dumps(sh, ensure_ascii=False)[:160] + f' 복사={len(cb)}')
    rec(g, '실제 카카오톡·문자 앱으로 넘어가는 화면', 'DEVICE', '갤럭시에서 확인(메시지는 보내지 않고 창만 확인)')
    c.close(); b.close()
st = {k: sum(1 for r in R if r['status'] == k) for k in ('PASS', 'FAIL', 'WARN', 'DEVICE')}
md = ['# 효자 2차 최종 보완 검수', f'- 전체 {len(R)}항목 · 통과 {st["PASS"]} · 실패 {st["FAIL"]} · 경고 {st["WARN"]} · 실기기 확인 필요 {st["DEVICE"]}', '', '| 구분 | 묶음 | 항목 | 상세 |', '|---|---|---|---|']
for r in R: md.append(f"| {r['status']} | {r['group']} | {r['name']} | {r['detail'].replace('|','/')[:120]} |")
open(OUT + '/report.md', 'w', encoding='utf8').write('\n'.join(md)); json.dump(R, open(OUT + '/report.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print(f'\n전체 {len(R)} · 통과 {st["PASS"]} · 실패 {st["FAIL"]} · 경고 {st["WARN"]} · 실기기 {st["DEVICE"]}')
sys.exit(1 if st['FAIL'] else 0)
