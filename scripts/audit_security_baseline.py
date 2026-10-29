"""Read-only security baseline audit. No secrets or network access."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]

def audit():
    issues = []
    workflow = ROOT / ".github/workflows/update-data.yml"
    if workflow.exists():
        s = workflow.read_text(encoding="utf-8")
        if "if: always()" in s and "git add data" in s:
            issues.append(("HIGH", "자동 수집 실패 후에도 data 커밋 단계 실행 가능", str(workflow.relative_to(ROOT))))
        if "contents: write" in s:
            issues.append(("REVIEW", "자동 갱신 workflow에 저장소 쓰기 권한 존재", str(workflow.relative_to(ROOT))))
    else:
        issues.append(("REVIEW", "자료 갱신 workflow를 찾지 못함", str(workflow.relative_to(ROOT))))
    script = ROOT / "scripts/fetch_data.py"
    if script.exists():
        s = script.read_text(encoding="utf-8")
        if "DATA_GO_KR_KEY" not in s:
            issues.append(("REVIEW", "API 키 환경변수 사용 여부 확인 필요", str(script.relative_to(ROOT))))
        if 'os.replace(' not in s:
            issues.append(("REVIEW", "원자적 파일 교체 여부 확인 필요", str(script.relative_to(ROOT))))
    else:
        issues.append(("REVIEW", "자료 수집 스크립트가 없음", str(script.relative_to(ROOT))))
    return issues

if __name__ == "__main__":
    issues = audit()
    print(json.dumps({"result": "review_required" if issues else "no_known_pattern_found",
                      "issues": [{"severity": s, "message": m, "path": p} for s,m,p in issues]},
                     ensure_ascii=False, indent=2))
    # Audit reports findings, does not block CI until baseline findings are resolved.
    sys.exit(0)
