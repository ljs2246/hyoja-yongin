#!/usr/bin/env python3
"""Noto Sans KR(구글 글꼴, SIL OFL)을 사이트에 직접 넣기 위한 변환 스크립트.
입력: google/fonts 저장소의 ofl/notosanskr/NotoSansKR[wght].ttf (가변 글꼴)
출력: fonts/noto-sans-kr-a.woff (자주 쓰는 글자) + fonts/noto-sans-kr-b.woff (나머지 한글) + fonts/noto-sans-kr.css
사용: python3 qa/tools/build_fonts.py <원본.ttf> <사이트폴더>
"""
import sys, os, re, glob
from fontTools.ttLib import TTFont
from fontTools import subset
from fontTools.varLib import instancer

src, root = sys.argv[1], os.path.abspath(sys.argv[2])
out = os.path.join(root, 'fonts'); os.makedirs(out, exist_ok=True)

# 1) 사이트에서 실제로 쓰는 글자 모으기
used = set()
for pat in ('*.html', '*.js', '*.css', 'data/*.json', 'docs/*.md'):
    for f in glob.glob(os.path.join(root, pat)):
        try: used |= set(open(f, encoding='utf-8').read())
        except Exception: pass
# 2) 자주 쓰는 한글 2,350자(KS X 1001) + 기본 문자
ksx = set()
for cp in range(0xAC00, 0xD7A4):
    try: chr(cp).encode('iso2022_kr'); ksx.add(cp)
    except UnicodeEncodeError: pass
base = set(range(0x20, 0x7F)) | set(range(0xA0, 0x100)) | set(range(0x2000, 0x2070)) | set(range(0x2190, 0x2200)) | set(range(0x2460, 0x2500)) | set(range(0x25A0, 0x2600)) | set(range(0x3000, 0x3040)) | set(range(0x3130, 0x3190)) | set(range(0x1100, 0x1200)) | set(range(0xFF00, 0xFFF0))
A = {ord(c) for c in used if ord(c) >= 0x20 and ord(c) not in range(0x7F, 0xA0)} | ksx | base
hangul_all = set(range(0xAC00, 0xD7A4))
B = hangul_all - A

f0 = TTFont(src)
cm = f0.getBestCmap()
A &= set(cm); B &= set(cm)
f0 = instancer.instantiateVariableFont(f0, {'wght': (400, 900)})   # 사용 굵기 400~900만
tmp = os.path.join(out, '_base.ttf'); f0.save(tmp)

def make(chars, name):
    opts = subset.Options(); opts.flavor = 'woff'; opts.layout_features = ['*']; opts.notdef_outline = True
    opts.name_IDs = ['*']; opts.hinting = False; opts.desubroutinize = True
    ft = TTFont(tmp); s = subset.Subsetter(opts); s.populate(unicodes=sorted(chars)); s.subset(ft)
    ft.flavor = 'woff'; p = os.path.join(out, name); ft.save(p); return p

def ranges(cps):
    cps = sorted(cps); res = []; s = p = None
    for c in cps:
        if s is None: s = p = c
        elif c == p + 1: p = c
        else: res.append((s, p)); s = p = c
    if s is not None: res.append((s, p))
    return ','.join(('U+%X' % a) if a == b else ('U+%X-%X' % (a, b)) for a, b in res)

pa = make(A, 'noto-sans-kr-a.woff'); pb = make(B, 'noto-sans-kr-b.woff'); os.remove(tmp)
css = f"""/* Noto Sans KR (SIL Open Font License 1.1, fonts/OFL.txt) — 사이트 자체 보관본. 구글 서버에 접속하지 않아요.
   b: 드물게 쓰는 한글(먼저 선언), a: 자주 쓰는 글자(나중에 선언해 우선 적용). 필요한 구간만 내려받아요. */
@font-face{{font-family:'Noto Sans KR';font-style:normal;font-weight:400 900;font-display:swap;src:url(noto-sans-kr-b.woff) format('woff');unicode-range:U+AC00-D7A3}}
@font-face{{font-family:'Noto Sans KR';font-style:normal;font-weight:400 900;font-display:swap;src:url(noto-sans-kr-a.woff) format('woff');unicode-range:{ranges(A)}}}
"""
open(os.path.join(out, 'noto-sans-kr.css'), 'w', encoding='utf-8').write(css)
print('A글자', len(A), os.path.getsize(pa), 'B글자', len(B), os.path.getsize(pb), 'css', len(css))
