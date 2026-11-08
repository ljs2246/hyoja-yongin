#!/bin/bash
# 전체 자동 검사 후 검수 보고서(docs/qa-report-latest.md) 생성. 실패가 있으면 종료코드 1.
cd "$(dirname "$0")/.." || exit 1
OUT=docs/qa-report-latest.md; FAIL=0
run(){ name="$1"; shift; if "$@" >/tmp/qa_$$.log 2>&1; then r="통과"; else r="실패"; FAIL=1; fi
  echo "| $name | $r | $(tail -1 /tmp/qa_$$.log | tr '|' '/') |" >> $OUT.tmp; }
echo "| 검사 | 결과 | 마지막 줄 |" > $OUT.tmp; echo "|---|---|---|" >> $OUT.tmp
run "가족 기능 단위검사" node tests/family.test.cjs
run "의료 지도 검사" node scripts/test-medical-maps.cjs
run "지역 핵심 검사" node scripts/test-region-core.cjs
run "지역 프로필 검사" node scripts/test-region-profiles.cjs
run "전화 링크 공식근거 검사" python3 scripts/check-phones.py
run "휴대폰 화면 모의검사" python3 tests/e2e-mobile.py
{ echo "# 자동 검수 보고서"; echo; echo "- 실행: $(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M') KST / 커밋 $(git rev-parse --short HEAD)"; echo "- 한계: 실제 Android·iPhone 검사는 포함되지 않음(미검증)"; echo "- 결과: $([ $FAIL = 0 ] && echo 전체 통과 || echo 실패 있음)"; echo; cat $OUT.tmp; } > $OUT; rm -f $OUT.tmp /tmp/qa_$$.log
cat $OUT; exit $FAIL
