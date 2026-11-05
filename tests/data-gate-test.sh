#!/bin/bash
# 자료 갱신 관문 시험: 실패·오래됨·건수 급감·미래 날짜·휴대폰 번호를 공개 반영 전에 막는지 확인 (임시 저장소에서 실행, 실제 자료 변경 없음)
set -u; ROOT=$(cd "$(dirname "$0")/.." && pwd); T=$(mktemp -d); P=0; F=0
ok(){ if [ "$1" = "$2" ]; then P=$((P+1)); echo "통과: $3"; else F=$((F+1)); echo "실패: $3 (기대 $2, 결과 $1)"; fi; }
mk(){ rm -rf "$T/r"; mkdir -p "$T/r/data" "$T/r/scripts"; cp "$ROOT/scripts/check-data.py" "$T/r/scripts/"; cd "$T/r"; git init -q
 python3 - "$1" <<'P'
import json,sys
rows=[{"dutyName":f"기관{i}","dutyTel1":"031-111-2222"} for i in range(10)]
for n in('emergency','pharmacy'):json.dump({"확인한 때":sys.argv[1],"건수":10,"목록":rows},open(f'data/{n}.json','w'),ensure_ascii=False)
json.dump({"emergency":{"상태":"성공"},"pharmacy":{"상태":"성공"}},open('data/status.json','w'))
P
 git add -A; git -c user.name=t -c user.email=t@t commit -qm base; }
run(){ python3 scripts/check-data.py --restore --fresh --now="2026-11-05 10:00" >/dev/null 2>&1; echo $?; }
rc(){ python3 scripts/check-data.py --fresh --now="2026-11-05 10:00" >/dev/null 2>&1; echo $?; }
mk "2026-11-05 06:30"; ok "$(rc)" 0 "오늘 수집한 정상 자료는 통과"
mk "2026-10-30 10:41"; ok "$(rc)" 1 "6일 지난 자료는 실패(공개 차단)"
mk "2026-11-05 06:30"; python3 -c "
import json;d=json.load(open('data/status.json'));d['pharmacy']={'상태':'실패','이유':'x'};json.dump(d,open('data/status.json','w'))"; ok "$(rc)" 1 "수집 실패 표시면 차단"
mk "2026-11-05 06:30"; sed -i 's/"확인한 때": "[^"]*", //' data/pharmacy.json; ok "$(rc)" 1 "확인일 없으면 차단"
mk "2026-11-09 06:30"; ok "$(rc)" 1 "미래 날짜는 차단"
mk "2026-11-05 06:30"; python3 -c "
import json;d=json.load(open('data/emergency.json'));d['목록'][0]['dutyTel1']='010-1234-5678';json.dump(d,open('data/emergency.json','w'),ensure_ascii=False)"; ok "$(rc)" 1 "휴대전화 번호 섞이면 차단"
mk "2026-11-05 06:30"; python3 -c "
import json;d=json.load(open('data/pharmacy.json'));d['목록']=d['목록'][:3];d['건수']=3;json.dump(d,open('data/pharmacy.json','w'),ensure_ascii=False)"; ok "$(rc)" 1 "건수 급감(10→3)은 차단"
# 복구: 오래된 새 자료를 --restore 하면 승인본으로 돌아가는지
mk "2026-11-05 06:30"; python3 -c "
import json;d=json.load(open('data/pharmacy.json'));d['확인한 때']='2026-10-01 00:00';json.dump(d,open('data/pharmacy.json','w'),ensure_ascii=False)"; run >/dev/null; ok "$(git diff --quiet && echo 0 || echo 1)" 0 "--restore 후 승인본으로 복구(변경 0)"
# 평소(--fresh 없음) CI 검사는 옛 자료를 실패로 만들지 않음
mk "2026-10-30 10:41"; python3 scripts/check-data.py >/dev/null 2>&1; ok "$?" 0 "평소 검사는 오래된 승인본을 막지 않음"
rm -rf "$T"; echo "자료 갱신 관문 시험: 통과 $P / 실패 $F"; [ $F -eq 0 ]
