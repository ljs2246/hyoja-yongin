#!/usr/bin/env python3
"""화면의 모든 tel: 링크가 공식 근거(출처 URL·확인일)를 가졌는지 검사. 미확인 번호가 있으면 실패(종료코드 1)."""
import re,glob,sys
bad=[]
for f in sorted(glob.glob('*.html')):
    s=open(f).read()
    for m in re.finditer(r'<a ([^>]*?)href="tel:(\d+)"([^>]*)>',s):
        a=m.group(1)+m.group(3)
        if 'data-hj-src="' not in a or 'data-hj-checked="' not in a: bad.append((f,m.group(2)))
# 광고주 번호는 사업자·계약 확인 전 어떤 형태로도 노출 금지(링크·텍스트)
HELD=['031-201-8571','0312018571','031-336-0040','0313360040','031-6193-5114','03161935114','031-6193-2114','03161932114','031-8021-2130','03180212130']  # 지시013: 공개 보류 번호(화면·스크립트·캐시 어디에도 노출 금지)
ADS=['031-321-3636','0313213636','031-338-7100','0313387100','070-7954-1967','07079541967']
for f in sorted(glob.glob('*.html')):
    t=open(f).read()
    for a in ADS:
        if a in t: bad.append((f,'광고주번호노출 '+a))
for f in sorted(glob.glob('*.html')+glob.glob('*.js')):
    t=open(f).read()
    for h in HELD:
        if h in t: bad.append((f,'공개 보류 번호 노출 '+h))
for f,n in bad: print('근거 없는 전화 링크:',f,n)
print('전화 링크 검사', '통과' if not bad else f'실패 {len(bad)}건')
sys.exit(1 if bad else 0)
