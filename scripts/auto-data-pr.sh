#!/bin/bash
# 공식정보 자동 갱신 → 검증 후 PR 방식(운영 main에 직접 올리지 않음).
# DRY_RUN=1(기본): 원격 push·PR 생성·검사 실행 요청을 전부 하지 않는다(무엇을 할지 출력만, 작업 폴더는 원래대로).
# DRY_RUN=0: 갱신 브랜치 push → PR 생성 → 필수 검사 'qa' 수동 실행 요청(자동 생성 PR은 검사가 저절로 안 돌기 때문) → 제한 시간 대기 후 결과 확인.
# 환경변수: PATHS(공백으로 구분, 기본 data 3개) PREFIX(기본 auto/data) CHECK(기본 python3 scripts/check-data.py --restore, none 이면 생략) BASE(main) QA_WORKFLOW(qa-test-branch.yml)
set -u; DRY_RUN=${DRY_RUN:-1}; BASE=${BASE:-main}; PREFIX=${PREFIX:-auto/data}; PATHS=${PATHS:-"data/emergency.json data/pharmacy.json data/status.json"}
CHECK=${CHECK:-"python3 scripts/check-data.py --restore"}; QA_WORKFLOW=${QA_WORKFLOW:-qa-test-branch.yml}
DAY=$(TZ=Asia/Seoul date +%Y%m%d); BR="$PREFIX-$DAY"
[ "$CHECK" = "none" ] || $CHECK || exit 1
git add $PATHS 2>/dev/null
git diff --cached --quiet && { echo "변경 없음: 아무것도 만들지 않음"; exit 0; }
if [ "$DRY_RUN" = "1" ]; then
  echo "DRY_RUN: 아래 변경을 $BR 브랜치로 올리고 PR을 만들 예정입니다(실제로는 아무것도 하지 않음)"; git diff --cached --stat | tail -5
  git reset -q; exit 0   # 스테이징만 되돌림(작업 파일은 그대로)
fi
if git ls-remote --exit-code --heads origin "$BR" >/dev/null 2>&1; then echo "중복 방지: $BR 이미 있음 → 건너뜀"; git reset -q; exit 0; fi
OPEN=$(gh pr list --state open --json headRefName --jq "[.[]|select(.headRefName|startswith(\"$PREFIX-\"))]|length" 2>/dev/null || echo 99)
[ "$OPEN" = "0" ] || { echo "중복 방지: 열린 갱신 PR이 이미 있음($OPEN) → 새로 만들지 않음"; git reset -q; exit 0; }
git checkout -q -b "$BR" && git -c user.name="자동 갱신" -c user.email="actions@users.noreply.github.com" commit -qm "자동 갱신(검증 통과): $PREFIX $DAY" || exit 1
git push -q origin "$BR" || { echo "푸시 실패(보호 규칙·권한 확인)"; exit 1; }
gh pr create --base "$BASE" --head "$BR" --title "자동 갱신: $PREFIX $DAY (검증 통과, 승인 대기)" --body "자료 검사 관문을 통과한 변경입니다. 필수 검사 qa 결과가 성공일 때만 병합하세요. 결과가 없거나 실패면 병합 금지. 자동 병합 없음." || exit 1
gh workflow run "$QA_WORKFLOW" --ref "$BR" || { echo "검사 실행 요청 실패 → 검사 결과가 없으므로 병합 금지 상태 유지"; exit 1; }
SHA=$(git rev-parse HEAD); bash "$(dirname "$0")/wait-qa.sh" "$SHA"
