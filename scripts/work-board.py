#!/usr/bin/env python3
"""작업 현황 통합 관리표: docs/automation/work-board.json 을 검사하고 docs/automation/work-board.md 로 만든다.
규칙: 상태는 5종만, '완료'는 증빙 파일이 저장소에 실제로 있어야 함, 작업명 중복 금지, 남은위험·다음조치 필수."""
import json,os,sys,collections
j=json.load(open('docs/automation/work-board.json'));ok={'완료','검수중','미검증','보류','미구현'};bad=[];seen=set()
for r in j['항목']:
    if r['상태'] not in ok:bad.append((r['작업'],'상태 값 오류'))
    if r['상태']=='완료' and not os.path.exists(r['증빙']):bad.append((r['작업'],'완료인데 증빙 파일 없음'))
    if r['작업'] in seen:bad.append((r['작업'],'작업명 중복'))
    seen.add(r['작업'])
    if not r['남은위험'] or not r['다음조치']:bad.append((r['작업'],'남은위험·다음조치 누락'))
for a,b in bad:print('관리표 검사 실패:',a,b)
c=collections.Counter(r['상태'] for r in j['항목'])
L=['# 작업 현황 통합 관리표 (자동 생성)',f"기준일 {j['기준일']} / 합계 {len(j['항목'])}건: "+' · '.join(f'{k} {c.get(k,0)}' for k in ['완료','검수중','미검증','보류','미구현']),'','| 부서 | 작업 | 상태 | 증빙 | 남은 위험 | 다음 조치 |','|---|---|---|---|---|---|']
L+=[f"| {r['부서']} | {r['작업']} | {r['상태']} | `{r['증빙']}` | {r['남은위험']} | {r['다음조치']} |" for r in j['항목']]
L+=['','상태 정의: '+' / '.join(f'{k}={v}' for k,v in j['상태정의'].items())]
open('docs/automation/work-board.md','w').write('\n'.join(L)+'\n')
print('관리표 검사','통과' if not bad else f'실패 {len(bad)}건',dict(c));sys.exit(1 if bad else 0)
