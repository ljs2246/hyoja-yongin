# 시험 PR #1 결과 (지시 018 ②) — 2026-10-30
- PR: https://github.com/ljs2246/hyoja-yongin/pull/1 (초안, 병합 금지 표시, 시험 후 닫음. main 변경 없음)
- PR 머리 커밋: ba624003af0cec973ee744c962ade86f84828b08 (브랜치 auto/test-pr-20261030)
- 사람이 연 PR 경로: 실행 41003453743 (이벤트 pull_request) → 검사 `qa` 성공
- 자동 생성 PR 경로(실행 요청): 실행 41003487771 (이벤트 workflow_dispatch, ref=시험 브랜치) → 검사 `qa` 성공, 같은 커밋(sha)에 붙음
- 병합 관문(scripts/pr-gate-check.py)에 실제 check-runs 응답을 넣은 결과: "통과: 필수 검사 qa 성공" (원본 JSON: test-pr1-check-runs-20261030.json)
- 별도 발견 1: 직전 푸시(c46d07d)의 `qa` 실패 = CI에 PyYAML 없음(실행 41002705053). 수정 후 11f41cb 에서 성공(실행 41003202547). 실제 CI에서만 드러난 결함.
- 별도 발견 2: 이 세션에서는 `gh pr create`(GraphQL)가 막혀 REST(gh api)로 PR을 만듦. GitHub Actions 안의 `gh pr create` 동작은 이번 시험에서 검증되지 않음(미검증).
- 한계: 로그 원문·산출물(artifact) 내려받기는 이 환경에서 막혀 있어 실행 번호와 JSON으로만 보존. 보호 규칙은 아직 적용 전이므로 "필수 검사 없이 병합 불가" 자체는 미검증.
