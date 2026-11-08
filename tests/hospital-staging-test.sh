#!/bin/bash
# 모의 XML(실제 병원 아님)로 파싱·선별·격리 시험 + 노출 차단 검사 + 위반 주입 시험
set -u; cd "$(dirname "$0")/.."; F=0; O=$(mktemp -d)/h.json
python3 scripts/fetch_hospitals.py --parse tests/fixtures/hospitals-sample.xml --out $O | tee /dev/stderr | grep -q "통과 2 / 제외 3" && echo "통과 선별: 용인 2건 통과, 중복·번호이상·타지역 3건 제외" || { echo "실패 선별"; F=1; }
env -u DATA_GO_KR_KEY python3 scripts/fetch_hospitals.py >/dev/null; [ $? = 2 ] && echo "통과 인증키 없으면 호출하지 않음" || { echo "실패 키 없음 처리"; F=1; }
python3 scripts/check-staging.py >/dev/null && echo "통과 현재 화면·서비스워커에 격리 자료 참조 없음" || { echo "실패 노출 점검"; F=1; }
cp sw.js $O.bak; sed -i "s#const CORE=\[#const CORE=['data/staging/hospitals-pending.json',#" sw.js; grep -q staging sw.js && { python3 scripts/check-staging.py >/dev/null && { echo "실패 위반 주입을 못 잡음"; F=1; } || echo "통과 서비스워커에 격리 파일을 넣으면 검사가 막음"; }; cp $O.bak sw.js
exit $F
