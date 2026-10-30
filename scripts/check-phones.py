#!/usr/bin/env python3
"""화면의 모든 tel: 링크가 공식 근거(출처 URL·확인일)를 가졌는지 검사. 미확인 번호가 있으면 실패(종료코드 1)."""
import re,glob,sys
bad=[]
for f in sorted(glob.glob('*.html')):
    s=open(f).read()
    for m in re.finditer(r'<a ([^>]*?)href="tel:(\d+)"([^>]*)>',s):
        a=m.group(1)+m.group(3)
        if 'data-hj-src="' not in a or 'data-hj-checked="' not in a: bad.append((f,m.group(2)))
for f,n in bad: print('근거 없는 전화 링크:',f,n)
print('전화 링크 검사', '통과' if not bad else f'실패 {len(bad)}건')
sys.exit(1 if bad else 0)
