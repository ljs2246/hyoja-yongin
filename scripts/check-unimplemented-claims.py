#!/usr/bin/env python3
"""구현되지 않은 기능을 공개 화면이 안내하지 않는지 검사(지시 11-05 P1-5: 구현되지 않은 기능은 공개 안내에서 제외).
금지 문구 목록은 docs/feature-status.json 의 '미구현' 항목에서 읽는다. 하나라도 화면(html)에 있으면 실패."""
import json,glob,sys
st=json.load(open('docs/feature-status.json',encoding='utf-8'))
bad=[w for x in st['기능'] if x['상태']=='미구현' for w in x.get('금지문구',[])]
hits=[]
for f in sorted(glob.glob('*.html')):
    t=open(f,encoding='utf-8').read()
    hits+=[(f,w) for w in bad if w in t]
for f,w in hits:print('미구현 기능 안내 발견:',f,w)
print('미구현 기능 안내 검사','통과' if not hits else f'실패 {len(hits)}건','(금지 문구',len(bad),'개)');sys.exit(1 if hits else 0)
