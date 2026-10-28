# 용인 응급의료기관·약국 자료를 공공데이터포털에서 받아 data/ 폴더에 저장합니다.
# 인증키는 환경변수 DATA_GO_KR_KEY 로만 읽고, 화면·기록에 절대 출력하지 않습니다.
import json, os, sys, time, urllib.parse, urllib.request, tempfile, shutil, re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

KEY = os.environ.get("DATA_GO_KR_KEY", "").strip()
BASE = "https://apis.data.go.kr/B552657"
GU = ["처인구", "기흥구", "수지구"]
KST = timezone(timedelta(hours=9))
OUT = os.path.join(os.path.dirname(__file__), "..", "data")

def call_page(path, params, page):
    q = {"serviceKey": KEY, "pageNo": str(page), "numOfRows": "200"}
    q.update(params)
    url = f"{BASE}/{path}?" + urllib.parse.urlencode(q, safe=":/")
    last = None
    for i in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                body = r.read()
            root = ET.fromstring(body)
            code = (root.findtext(".//resultCode") or "").strip()
            if code not in ("00", ""):
                raise RuntimeError("API 결과 코드 " + code + " " + (root.findtext(".//resultMsg") or ""))
            items = [{c.tag: (c.text or "").strip() for c in it} for it in root.iter("item")]
            total_text = root.findtext(".//totalCount")
            total = int(total_text) if total_text is not None else None
            if total is not None and total < 0:
                raise ValueError("invalid totalCount")
            return items, total
        except Exception as e:  # 키가 들어간 주소는 오류 문구에 넣지 않음
            last = "공공데이터 요청 실패 (" + type(e).__name__ + ")"
            time.sleep(3)
    raise RuntimeError(last)

def call(path, params):
    rows = []
    expected_total = None
    previous_page = None
    for page in range(1, 1001):
        items, total = call_page(path, params, page)
        if page == 1:
            expected_total = total
        elif total != expected_total:
            raise RuntimeError("조회 중 자료 건수가 바뀌어 기존 자료를 유지합니다.")
        if items and items == previous_page:
            raise RuntimeError("같은 페이지가 반복되어 기존 자료를 유지합니다.")
        rows.extend(items)
        if expected_total is not None:
            if len(rows) == expected_total:
                return rows
            if not items or len(rows) > expected_total:
                raise RuntimeError("전체 건수와 수집 건수가 달라 기존 자료를 유지합니다.")
        elif len(items) < 200:
            return rows
        previous_page = items
    raise RuntimeError("페이지 한도를 초과하여 기존 자료를 유지합니다.")

def fetch(path, label):
    rows = []
    for gu in GU:
        got = []
        for q1 in (f"용인시 {gu}", f"용인시{gu}"):
            got = call(path, {"Q0": "경기도", "Q1": q1})
            if got:
                break
        print(f"{label} {gu}: {len(got)}건")
        if len(got) == 0:
            raise RuntimeError("district data missing")
        rows += got
    return rows

def validate(name, rows):
    """Reject malformed or suspicious datasets before touching published files."""
    if not rows:
        raise ValueError(name + ": empty result")
    seen = set()
    for row in rows:
        identifier = str(row.get("hpid", "")).strip()
        address = str(row.get("dutyAddr", "")).strip()
        title = str(row.get("dutyName", "")).strip()
        if not identifier or not title or not address:
            raise ValueError(name + ": missing required field")
        if identifier in seen:
            raise ValueError(name + ": repeated institution identifier")
        seen.add(identifier)
        if not re.match(r"^경기도\s+용인시\s+(처인구|기흥구|수지구)(?:\s|$)", address):
            raise ValueError(name + ": out-of-region address")
    return len(rows)


def main():
    if not KEY:
        raise RuntimeError("DATA_GO_KR_KEY missing; published data unchanged")
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    pending = {}
    for name, path, label in [
        ("emergency", "ErmctInfoInqireService/getEgytListInfoInqire", "응급의료기관"),
        ("pharmacy", "ErmctInsttInfoInqireService/getParmacyListInfoInqire", "약국"),
    ]:
        rows = fetch(path, label)
        validate(name, rows)
        pending[name] = {"확인한 때": now, "건수": len(rows), "목록": rows}

    # One validated snapshot is committed by the workflow. No partial writes
    # occur before all required API calls and validation finish.
    os.makedirs(OUT, exist_ok=True)
    status = {"확인한 때": now, "출처": "국립중앙의료원(공공데이터포털)",
              "emergency": {"상태": "성공", "건수": len(pending["emergency"]["목록"])},
              "pharmacy": {"상태": "성공", "건수": len(pending["pharmacy"]["목록"])}}
    stage = tempfile.mkdtemp(prefix=".medical-stage-", dir=OUT)
    try:
        for name, payload in [("emergency", pending["emergency"]),
                              ("pharmacy", pending["pharmacy"]), ("status", status)]:
            with open(os.path.join(stage, name + ".json"), "w", encoding="utf-8") as out:
                json.dump(payload, out, ensure_ascii=False, indent=1)
        for name in ("emergency", "pharmacy", "status"):
            os.replace(os.path.join(stage, name + ".json"), os.path.join(OUT, name + ".json"))
    finally:
        shutil.rmtree(stage, ignore_errors=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("자료 갱신 중단: " + type(exc).__name__ + "; 기존 공개 자료 유지")
        sys.exit(1)
