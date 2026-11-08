#!/bin/bash
# 3차 안전망: 백업이 '있다'가 아니라 '실제로 복원된다'를 확인한다. (원본 저장소는 읽기만 하고 바꾸지 않음)
# 1) 전체 번들을 만들어 빈 폴더에 복제 → 커밋 번호·객체 무결성 일치  2) 복제본에서 핵심 시험 실행
# 3) 패치만으로 복원: 기준 커밋 위에 패치를 적용했을 때 결과 폴더 내용이 원본과 같은지  4) 결과를 docs/backup-restore-latest.json에 기록
# 사용: bash scripts/backup-restore-test.sh [기준커밋(기본 1d610a1)]   종료코드 0=복원 가능, 1=복원 불가
set -u; ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"; BASE=${1:-1d610a1}; BR=$(git rev-parse --abbrev-ref HEAD); HEAD_SHA=$(git rev-parse HEAD)
T=$(mktemp -d); P=0; F=0; OUT=()
ok(){ if [ "$1" = "0" ]; then P=$((P+1)); OUT+=("통과: $2"); echo "통과: $2"; else F=$((F+1)); OUT+=("실패: $2"); echo "실패: $2"; fi; }
git bundle create "$T/full.bundle" "$BR" >/dev/null 2>&1; ok $? "전체 번들 생성"
sha256sum "$T/full.bundle" > "$T/full.sha"; BSHA=$(cut -c1-64 "$T/full.sha")
git bundle verify "$T/full.bundle" >/dev/null 2>&1; ok $? "번들 자체 검증"
git clone -q -b "$BR" "$T/full.bundle" "$T/restore" 2>/dev/null; ok $? "빈 폴더에 복제(복원)"
[ "$(git -C "$T/restore" rev-parse HEAD 2>/dev/null)" = "$HEAD_SHA" ]; ok $? "복원본 커밋 번호가 원본과 같음($HEAD_SHA)"
git -C "$T/restore" fsck --no-progress >/dev/null 2>&1; ok $? "복원본 객체 무결성(fsck)"
( cd "$T/restore" && node scripts/test-medical-maps.cjs >/dev/null 2>&1 ); ok $? "복원본에서 의료 지도·전화 숨김 시험"
( cd "$T/restore" && bash tests/data-gate-test.sh >/dev/null 2>&1 ); ok $? "복원본에서 자료 갱신 관문 시험"
( cd "$T/restore" && python3 scripts/check-phones.py >/dev/null 2>&1 ); ok $? "복원본에서 전화 링크 공식근거 검사"
( cd "$T/restore" && python3 scripts/pharmacy-phone-ledger.py check >/dev/null 2>&1 ); ok $? "복원본에서 약국 전화 검증대장 검사"
( cd "$T/restore" && python3 tests/offline-stale-test.py >/dev/null 2>&1 ); ok $? "복원본에서 오프라인 옛 저장본 시험"
# 패치만으로 복원
git format-patch --stdout "$BASE..HEAD" > "$T/all.patch" 2>/dev/null; [ -s "$T/all.patch" ]; ok $? "패치 파일 생성($(wc -c < "$T/all.patch") bytes)"
git clone -q "$T/full.bundle" "$T/pr" 2>/dev/null && git -C "$T/pr" checkout -q "$BASE" 2>/dev/null && git -C "$T/pr" -c user.name=t -c user.email=t@t am -q "$T/all.patch" >/dev/null 2>&1; ok $? "기준 커밋 위에 패치 적용(git am)"
[ "$(git -C "$T/pr" rev-parse 'HEAD^{tree}' 2>/dev/null)" = "$(git rev-parse 'HEAD^{tree}')" ]; ok $? "패치 복원 결과 폴더 내용이 원본과 같음(트리 해시 일치)"
rm -rf "$T/restore" "$T/pr"
python3 - "$HEAD_SHA" "$BR" "$BSHA" "$P" "$F" "$(printf '%s\n' "${OUT[@]}")" <<'PY'
import json,sys,datetime
h,b,s,p,f,o=sys.argv[1:7]
json.dump({'기록시각':datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),'브랜치':b,'원본커밋':h,'번들sha256':s,'통과':int(p),'실패':int(f),'복원가능':int(f)==0,'항목':o.split('\n'),'비고':'원본 코드는 바꾸지 않음. 모의 환경 시험이며 실기기 시험이 아님.'},open('docs/backup-restore-latest.json','w'),ensure_ascii=False,indent=1)
PY
rm -rf "$T"; echo "백업 복원 시험: 통과 $P / 실패 $F"; [ $F -eq 0 ]
