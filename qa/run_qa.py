#!/usr/bin/env python3
"""효자 용인 휴대폰 자동검수기 (Playwright, 무료).

실행:  python3 qa/run_qa.py [--out qa-report] [--root .] [--only 그룹이름]
결과:  qa-report/report.md, report.json, screenshots/*.png(실패한 항목만)
종료코드: 실패가 1건이라도 있으면 1 (통과 처리 없음). 경고(WARN)는 통과로 세되 보고서에 따로 적는다.
이 검수기는 파일을 고치거나 배포하지 않고, 외부 서버로 아무것도 보내지 않는다(글꼴 서버 요청은 차단).
"""
import argparse, json, os, re, sys, threading, http.server, socketserver, functools, datetime
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument('--root', default='.')
ap.add_argument('--out', default='qa-report')
ap.add_argument('--only', default='')
a = ap.parse_args()
ROOT = os.path.abspath(a.root)
OUT = os.path.abspath(a.out)
SHOTS = os.path.join(OUT, 'screenshots')
os.makedirs(SHOTS, exist_ok=True)
CFG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qa_config.json'), encoding='utf-8'))
PAGES, WIDTHS, SIZES, TOL = CFG['pages'], CFG['widths'], CFG['sizes'], CFG['overflow_tolerance_px']
ALLOW, BLOCK, EM_ALLOW = set(CFG['allow_static']), CFG['block'], set(CFG['emergency_search_allow'])
SIZE_KO = {'normal': '보통', 'large': '크게', 'xl': '아주 크게'}

R = []  # 결과 목록


def rec(group, name, status, detail='', shot=None):
    R.append({'group': group, 'name': name, 'status': status, 'detail': detail, 'shot': shot})
    mark = {'PASS': '통과', 'FAIL': '실패', 'WARN': '경고'}[status]
    if status != 'PASS':
        print(f'[{mark}] {group} · {name} · {detail}')


def shot(pg, key):
    safe = re.sub(r'[^0-9A-Za-z가-힣_.-]+', '_', key)[:90]
    p = os.path.join(SHOTS, safe + '.png')
    try:
        pg.screenshot(path=p, full_page=True)
        return 'screenshots/' + safe + '.png'
    except Exception:
        return None


def digits_tokens(text):
    return {re.sub(r'\D', '', t) for t in re.findall(r'\d[\d\-\s]{5,}\d', text)}


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *x):
        pass


handler = functools.partial(Quiet, directory=ROOT)
httpd = socketserver.TCPServer(('127.0.0.1', 0), handler)
PORT = httpd.server_address[1]
threading.Thread(target=httpd.serve_forever, daemon=True).start()
U = f'http://127.0.0.1:{PORT}/'


def want(g):
    return (not a.only) or a.only == g


def new_page(b, w, size='normal', h=800):
    ctx = b.new_context(viewport={'width': w, 'height': h}, has_touch=True, is_mobile=True, device_scale_factor=2)
    pg = ctx.new_page()
    pg.route(re.compile(r'.*(fonts\.googleapis|fonts\.gstatic).*'), lambda r: r.abort())
    pg.goto(U + 'index.html')
    pg.evaluate("k=>{try{localStorage.setItem('hyoja-size',k)}catch(e){}}", size)
    return ctx, pg


with sync_playwright() as p:
    b = p.chromium.launch()

    # ── 1. 14개 화면 열림 ──
    if want('화면'):
        ctx, pg = new_page(b, 390)
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:120]))
        bad_req = []
        pg.on('response', lambda r: bad_req.append(r.url) if r.status >= 400 and r.url.startswith(U) else None)
        for name in PAGES:
            errs.clear(); bad_req.clear()
            pg.goto(U + name + '.html'); pg.wait_for_timeout(300)
            info = pg.evaluate("({t:document.title,n:document.body.innerText.trim().length})")
            ok = info['t'] and info['n'] > 50 and not errs and not bad_req
            rec('화면', f'{name}.html 열림', 'PASS' if ok else 'FAIL',
                '' if ok else f"제목={info['t']!r} 글자수={info['n']} 스크립트오류={errs[:2]} 없는파일={bad_req[:2]}",
                None if ok else shot(pg, f'open_{name}'))
        ctx.close()

    # ── 2. 화면 폭 × 글자 크기 ──
    if want('폭·글자'):
        for w in WIDTHS:
            for size in SIZES:
                ctx, pg = new_page(b, w, size)
                for name in PAGES:
                    pg.goto(U + name + '.html'); pg.wait_for_timeout(250)
                    r = pg.evaluate("""()=>{const W=document.documentElement.clientWidth;let clip=0;
                      document.querySelectorAll('a[href^="tel:"],[data-hj-blocked]').forEach(a=>{const b=a.getBoundingClientRect();
                        const sp=[...a.querySelectorAll('span')].some(s=>s.getBoundingClientRect().right>b.right+1);
                        if(b.right>W+1||b.left<-1||sp)clip++});
                      return {sw:document.documentElement.scrollWidth,W,clip}}""")
                    key = f'{w}px · {SIZE_KO[size]} · {name}'
                    ov = r['sw'] - r['W']
                    if r['clip']:
                        rec('폭·글자', key, 'FAIL', f"번호 칸 잘림 {r['clip']}곳", shot(pg, f'clip_{w}_{size}_{name}'))
                    elif ov > TOL:
                        rec('폭·글자', key, 'FAIL', f"가로 넘침 {ov}px (너비 {r['sw']}/{r['W']})", shot(pg, f'over_{w}_{size}_{name}'))
                    elif ov > 0:
                        rec('폭·글자', key, 'WARN', f'가로 {ov}px 어긋남(허용 {TOL}px 이내) — 실기기 확인 권장', shot(pg, f'warn_{w}_{size}_{name}'))
                    else:
                        rec('폭·글자', key, 'PASS')
                ctx.close()

    # ── 3. 전화 버튼·미확인 번호 ──
    if want('전화'):
        ctx, pg = new_page(b, 390)
        for name in PAGES:
            pg.goto(U + name + '.html'); pg.wait_for_timeout(250)
            tels = pg.evaluate("[...document.querySelectorAll('a[href^=\"tel:\"]')].map(a=>a.getAttribute('href').slice(4).replace(/\\D/g,''))")
            shown = digits_tokens(pg.evaluate('document.body.innerText'))
            out = sorted({t for t in tels if t not in ALLOW})
            hid = sorted({t for t in set(tels) | shown if t in BLOCK})
            if out or hid:
                rec('전화', f'{name}.html 전화 링크', 'FAIL',
                    f'공식 확인 목록 밖 {out} / 숨겨야 할 번호 노출 {hid}', shot(pg, f'tel_{name}'))
            else:
                rec('전화', f'{name}.html 전화 링크 {len(tels)}개', 'PASS')
        pg.goto(U + 'Centers.html'); pg.wait_for_timeout(250)
        c = pg.evaluate("({tel:document.querySelectorAll('a[href^=\"tel:\"]').length,blk:[...document.querySelectorAll('[data-hj-blocked]')].map(e=>e.innerText)})")
        ok = c['tel'] == CFG['centers']['tel_count'] and len(c['blk']) == CFG['centers']['blocked_count'] and all(CFG['centers']['blocked_text'] in t for t in c['blk'])
        rec('전화', f"주민센터 전화 {c['tel']}개 + 공식 확인 중 {len(c['blk'])}개", 'PASS' if ok else 'FAIL',
            '' if ok else f"기대값 {CFG['centers']}", None if ok else shot(pg, 'centers_counts'))
        # 주민센터는 검색창이 없는 목록형이므로 동 이름 목록으로 대신 점검
        names = pg.evaluate("[...document.querySelectorAll('a[href^=\"tel:\"],[data-hj-blocked]')].length")
        rec('전화', '주민센터 목록 전체(전화+확인중) 39개', 'PASS' if names == 39 else 'FAIL', '' if names == 39 else f'{names}개')
        ctx.close()

    # ── 4. 병원·약국 검색 ──
    if want('검색'):
        ctx, pg = new_page(b, 390)
        pg.goto(U + 'Emergency.html'); pg.wait_for_selector('#medicalKind')

        def search(kind, gu, q=''):
            pg.select_option('#medicalKind', kind); pg.select_option('#medicalGu', gu)
            pg.fill('#medicalQuery', q); pg.click('#medicalSearchForm button[type=submit]'); pg.wait_for_timeout(600)
            for _ in range(80):
                m = pg.locator('#medicalSearchMore')
                if m.is_visible():
                    m.click(); pg.wait_for_timeout(40)
                else:
                    break
            return pg.evaluate("""()=>{const c=[...document.querySelectorAll('#medicalSearchResults article')];
              return {cards:c.length,tel:[...document.querySelectorAll('#medicalSearchResults a[href^=tel]')].map(a=>a.getAttribute('href').slice(4)),
              maps:document.querySelectorAll('#medicalSearchResults a[href*="map"],#medicalSearchResults a[href*="kakao"],#medicalSearchResults a[href*="naver"],#medicalSearchResults a[href*="google"]').length,
              status:(document.getElementById('medicalSearchStatus')||{}).innerText||''}}""")
        cases = [('pharmacy', g, '') for g in ('', '처인구', '기흥구', '수지구')] + [('pharmacy', '', '동백중앙로'), ('pharmacy', '', '약국'),
                 ('emergency', '', ''), ('emergency', '처인구', ''), ('emergency', '기흥구', ''), ('emergency', '수지구', '')]
        for kind, gu, q in cases:
            r = search(kind, gu, q)
            label = f"{'약국' if kind == 'pharmacy' else '응급의료기관'} · {gu or '전체'}{' · ' + q if q else ''}"
            probs = []
            if kind == 'pharmacy':
                if r['tel']: probs.append(f"약국 전화 버튼 {len(r['tel'])}개 노출")
                if r['cards'] == 0: probs.append('결과 0건')
            else:
                bad = [t for t in r['tel'] if t not in EM_ALLOW]
                if bad: probs.append(f'승인 목록 밖 번호 {bad}')
                if r['cards'] == 0 and '찾지 못했어요' not in r['status']: probs.append('결과 0건인데 안내 문구 없음')
            if r['cards'] and r['maps'] == 0: probs.append('지도 버튼 없음')
            rec('검색', label + f" ({r['cards']}건)", 'FAIL' if probs else 'PASS', ' / '.join(probs), shot(pg, 'search_' + label) if probs else None)
        # 응급 화면 '지금 문 연 약국' 목록
        pg.goto(U + 'Emergency.html'); pg.wait_for_selector('button.gu')
        for gu in ('처인구', '기흥구', '수지구'):
            pg.click(f'button.gu[data-gu={gu}]'); pg.wait_for_timeout(500)
            r = pg.evaluate("({items:document.querySelectorAll('#phList > *').length,tel:document.querySelectorAll('#phList a[href^=tel]').length})")
            probs = []
            if r['tel']: probs.append(f"전화 버튼 {r['tel']}개 노출")
            if r['items'] == 0: probs.append('목록 0건')
            rec('검색', f'지금 문 연 약국 · {gu} ({r["items"]}건)', 'FAIL' if probs else 'PASS', ' / '.join(probs), shot(pg, 'phlist_' + gu) if probs else None)
        ctx.close()

    # ── 5. 오프라인 캐시·재접속 ──
    if want('오프라인'):
        ctx, pg = new_page(b, 390)
        pg.goto(U + 'index.html'); pg.wait_for_timeout(1500)
        for name in PAGES:
            pg.goto(U + name + '.html'); pg.wait_for_timeout(250)
        pg.goto(U + 'index.html'); pg.wait_for_timeout(1500)
        sw = pg.evaluate("navigator.serviceWorker.controller?navigator.serviceWorker.controller.scriptURL.split('/').pop():null")
        caches_ = pg.evaluate("caches.keys()")
        rec('오프라인', '서비스워커 작동·저장소 생성', 'PASS' if sw == 'sw.js' and caches_ else 'FAIL', f'sw={sw} 저장소={caches_}',
            None if sw == 'sw.js' and caches_ else shot(pg, 'offline_sw'))
        ctx.set_offline(True)
        for name in PAGES:
            try:
                pg.goto(U + name + '.html', timeout=15000); pg.wait_for_timeout(300)
                n = pg.evaluate('document.body.innerText.trim().length')
                rec('오프라인', f'{name}.html 비행기 모드에서 열림', 'PASS' if n > 50 else 'FAIL', '' if n > 50 else f'글자수 {n}', None if n > 50 else shot(pg, f'offline_{name}'))
            except Exception as e:
                rec('오프라인', f'{name}.html 비행기 모드에서 열림', 'FAIL', str(e)[:100])
        ctx.set_offline(False)
        pg.goto(U + 'Centers.html'); pg.wait_for_timeout(500)
        n = pg.evaluate("document.querySelectorAll('a[href^=\"tel:\"]').length")
        rec('오프라인', '재접속 후 주민센터 전화 37개 복원', 'PASS' if n == 37 else 'FAIL', '' if n == 37 else f'{n}개')
        ctx.close()
    b.close()
httpd.shutdown()

# ── 보고서 ──
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M KST')
groups = {}
for r in R:
    groups.setdefault(r['group'], []).append(r)
tot = {s: sum(1 for r in R if r['status'] == s) for s in ('PASS', 'WARN', 'FAIL')}
L = [f'# 효자 용인 휴대폰 자동검수 보고서', f'- 실행: {now}', f'- 전체 {len(R)}항목 · 통과 {tot["PASS"]} · 경고 {tot["WARN"]} · 실패 {tot["FAIL"]}',
     f'- 결론: **{"실패 있음 — 통과 처리 불가" if tot["FAIL"] else "실패 없음 (경고는 아래 확인)"}**', '',
     '| 묶음 | 항목 | 통과 | 경고 | 실패 |', '|---|---|---|---|---|']
for g, rs in groups.items():
    L.append(f'| {g} | {len(rs)} | ' + ' | '.join(str(sum(1 for r in rs if r["status"] == s)) for s in ("PASS", "WARN", "FAIL")) + ' |')
for title, st in (('실패 목록', 'FAIL'), ('경고 목록', 'WARN')):
    xs = [r for r in R if r['status'] == st]
    if xs:
        L += ['', f'## {title}']
        for r in xs:
            L.append(f"- {r['group']} · {r['name']} — {r['detail']}" + (f" (캡처: {r['shot']})" if r['shot'] else ''))
open(os.path.join(OUT, 'report.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
json.dump({'time': now, 'totals': tot, 'results': R}, open(os.path.join(OUT, 'report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n'.join(L[:8]))
sys.exit(1 if tot['FAIL'] else 0)
