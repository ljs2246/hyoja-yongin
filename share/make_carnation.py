import math, random
random.seed(7)
def petal(a, r, w, fill, teeth=5):
    # 끝이 톱니처럼 주름진 카네이션 꽃잎 (위쪽을 향함)
    x0,y0=-w/2,-r*0.78
    pts=[f'M0 4 C{-w*0.55:.1f} {-r*0.25:.1f} {x0-2:.1f} {y0:.1f} {x0:.1f} {y0:.1f}']
    for i in range(teeth):
        xa=x0+w*(i+0.5)/teeth; xb=x0+w*(i+1)/teeth
        pk=-r-random.uniform(-2.5,2.5)
        pts.append(f'Q{xa:.1f} {pk:.1f} {xb:.1f} {y0-2:.1f}')
    pts.append(f'C{w*0.55+2:.1f} {-r*0.25:.1f} {w*0.55:.1f} {-r*0.1:.1f} 0 4Z')
    return f'<g transform="rotate({a:.1f})"><path d="{" ".join(pts)}" fill="{fill}" stroke="#8E1812" stroke-width="1" stroke-linejoin="round"/><path d="M0 -2 L0 {-r*0.7:.1f}" stroke="rgba(110,18,13,.35)" stroke-width="1.4" fill="none"/></g>'
def head():
    o=[]
    for a in range(-80,81,20): o.append(petal(a,50,30,'url(#c1)'))
    for a in range(-70,71,20): o.append(petal(a,45,28,'url(#c2)'))
    for a in range(-55,56,22): o.append(petal(a,38,26,'url(#c3)'))
    for a in (-25,0,25): o.append(petal(a,28,22,'url(#c4)',4))
    return ''.join(o)
H=head()
DEFS='''<svg width="0" height="0"><defs>
<linearGradient id="c1" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#8E1812"/><stop offset=".5" stop-color="#D93A30"/><stop offset="1" stop-color="#FF9A90"/></linearGradient>
<linearGradient id="c2" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#9E1B15"/><stop offset=".5" stop-color="#E8493E"/><stop offset="1" stop-color="#FFB3AB"/></linearGradient>
<linearGradient id="c3" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#A81F18"/><stop offset=".55" stop-color="#F0584B"/><stop offset="1" stop-color="#FFC8C1"/></linearGradient>
<linearGradient id="c4" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#B3261E"/><stop offset=".6" stop-color="#F26A5E"/><stop offset="1" stop-color="#FFD7D2"/></linearGradient>
<linearGradient id="st" x1="0" x2="1"><stop offset="0" stop-color="#1F5E2B"/><stop offset=".5" stop-color="#6FD07B"/><stop offset="1" stop-color="#1F5E2B"/></linearGradient>
<linearGradient id="lf" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9BEA9F"/><stop offset="1" stop-color="#2A7A37"/></linearGradient>
</defs></svg>'''
CAL='<path d="M-11 2 C-14 14 -8 24 0 28 C8 24 14 14 11 2 C6 7 -6 7 -11 2Z" fill="url(#lf)" stroke="#fff" stroke-width="1.2"/><path d="M-11 2 L-17 -4 L-8 0Z M11 2 L17 -4 L8 0Z M0 6 L0 -2 L-3 4Z" fill="#3E9A4A" stroke="#fff" stroke-width=".8"/>'
STEM='<path d="M0 26 C-5 52 5 76 -1 104" stroke="url(#st)" stroke-width="6" fill="none" stroke-linecap="round"/><path d="M-1 70 C-24 62 -36 68 -40 52 C-24 48 -7 56 -1 70Z" fill="url(#lf)" stroke="#fff" stroke-width="1.4"/><path d="M1 84 C22 76 34 79 41 64 C24 60 7 68 1 84Z" fill="url(#lf)" stroke="#fff" stroke-width="1.4"/>'
def carn(size,x,y,rot=0,stem=True):
    return f'<svg style="position:absolute;left:{x}px;top:{y}px;overflow:visible;filter:drop-shadow(0 8px 5px rgba(70,15,8,.45))" width="{size}" height="{size*1.6:.0f}" viewBox="-60 -62 120 192"><g transform="rotate({rot})">{STEM if stem else ""}{CAL}{H}</g></svg>'
if __name__=='__main__':
    def cell(label,seal_style,fs,cs):
        return f'<div class="c"><div class="w"><div class="s" style="{seal_style};font-size:{fs}px">효</div>{cs}</div><div class="n">{label}</div></div>'
    cells=[cell('① 오른쪽 위','border-radius:34px',120,carn(130,112,-82,-25)),
     cell('② 왼쪽 아래','border-radius:34px',120,carn(120,-52,92,-15,False)),
     cell('③ 동그라미 + 줄기','border-radius:50%',120,carn(125,116,42,-25)),
     cell('④ 낙관 + 위쪽','border-radius:10px;outline:6px solid #fff;outline-offset:-22px',104,carn(110,45,-64,0,False)),
     cell('⑤ 기울임','border-radius:34px;transform:rotate(-6deg)',120,carn(130,110,-82,-25)),
     cell('⑥ 아래 가운데','border-radius:34px',120,carn(105,48,145,0,False))]
    html=f'''<!doctype html><meta charset="utf-8"><body style="margin:0;background:#FFF6E8;font-family:'Noto Sans CJK KR',sans-serif">{DEFS}
<style>.g{{display:grid;grid-template-columns:repeat(3,1fr);gap:70px 20px;padding:90px 36px 50px;width:1000px;box-sizing:border-box}}
.c{{text-align:center}}.w{{position:relative;width:200px;height:200px;margin:0 auto}}.n{{font-size:24px;font-weight:700;color:#5A3300;margin-top:46px}}
.s{{width:200px;height:200px;display:flex;align-items:center;justify-content:center;font-family:'Noto Serif CJK KR',serif;font-weight:900;color:#fff;background:linear-gradient(160deg,#FF7A6C 0%,#D23A2F 45%,#9E1B15 100%);
box-shadow:0 14px 0 #5E0F0A,0 24px 30px rgba(70,15,8,.45),inset 0 6px 0 rgba(255,255,255,.4),inset 0 -10px 18px rgba(60,5,0,.35);text-shadow:0 5px 0 #8E1812,0 9px 10px rgba(50,0,0,.4)}}</style>
<div style="padding:30px 36px 0;font-size:34px;font-weight:800;color:#5A3300">입체 도장 「효」 + 카네이션 시안 (새 꽃)</div>
<div class="g">{"".join(cells)}</div>
<div style="padding:0 36px 40px;display:flex;gap:40px;align-items:flex-end"><div style="position:relative;width:260px;height:340px">{carn(260,0,10,0)}</div><div style="font-size:24px;color:#5A3300;font-weight:700">꽃 크게 보기</div></div>'''
    open('seals_carnation2.html','w',encoding='utf-8').write(html)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/opt/pw-browsers/chromium');pg=b.new_page(viewport={'width':1000,'height':900})
        pg.goto('file:///home/claude/hyoja-yongin/share/seals_carnation2.html');pg.wait_for_timeout(500);pg.screenshot(path='hyo_seal_carnation2.png',full_page=True)
