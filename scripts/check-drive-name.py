#!/usr/bin/env python3
"""드라이브 파일명 규칙 검사: [상태]_YYYY-MM-DD_번호_담당자_내용_vNN . 인자: 파일명들 또는 stdin 줄. 중복(같은 날짜·번호·내용의 다른 버전 제외) 감지."""
import re,sys
R=re.compile(r'^\[신규-(작업중|검수중|승인완료|보류)\]_(\d{4})-(\d{2})-(\d{2})_(\d{3})_([^_]+)_(.+)_v(\d{2})(\.[A-Za-z0-9]+)?$')
names=sys.argv[1:] or [l.strip() for l in sys.stdin if l.strip()]
bad=0;seen={}
for n in names:
    m=R.match(n)
    if not m: print('규칙 위반:',n);bad+=1;continue
    key=m.group(2,3,4,5,6,7)
    if (key,m.group(8)) in seen: print('중복:',n,'=',seen[(key,m.group(8))]);bad+=1
    seen[(key,m.group(8))]=n
print('파일명 검사','통과' if not bad else f'실패 {bad}건');sys.exit(1 if bad else 0)
