"""Collect the official region registry without changing live region choices."""
import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ENDPOINT = "https://apis.data.go.kr/1741000/StanReginCd/getStanReginCdList"
SOURCE = "https://www.data.go.kr/data/15077871/openapi.do"
OUT = Path(__file__).resolve().parent.parent / "data"


def parse(body):
    root = ET.fromstring(body)
    code = root.findtext(".//resultCode")
    if code != "INFO-0":
        raise ValueError("공식 API 성공 응답을 확인하지 못함")
    total = int(root.findtext(".//totalCount") or "-1")
    if total < 0:
        raise ValueError("전체 건수 누락")
    rows = [{c.tag: (c.text or "").strip() for c in row} for row in root.findall(".//row")]
    return rows, total


def validate(rows):
    index = {}
    for row in rows:
        code = row.get("region_cd", "")
        parent = row.get("locathigh_cd", "")
        if len(code) != 10 or not code.isdigit() or code == "0000000000":
            raise ValueError("지역코드 형식 오류")
        if code in index or not row.get("locatadd_nm"):
            raise ValueError("지역코드 중복 또는 지역명 누락")
        if len(parent) != 10 or not parent.isdigit():
            raise ValueError("상위지역코드 누락")
        index[code] = row
    for code, row in index.items():
        seen = set()
        current = code
        while current != "0000000000":
            if current in seen or current not in index:
                raise ValueError("지역 상위관계 순환 또는 누락")
            seen.add(current)
            current = index[current]["locathigh_cd"]
    return rows


def collect(key, request=None):
    request = request or urllib.request.urlopen
    rows, expected, previous = [], None, None
    for page in range(1, 1001):
        params = {"ServiceKey": urllib.parse.unquote(key), "pageNo": str(page),
                  "numOfRows": "200", "type": "xml"}
        url = ENDPOINT + "?" + urllib.parse.urlencode(params)
        with request(url, timeout=30) as response:
            items, total = parse(response.read())
        if expected is None:
            expected = total
        if total != expected or (items and items == previous):
            raise ValueError("조회 중 건수 변경 또는 페이지 반복")
        rows.extend(items)
        if len(rows) == expected:
            if not rows:
                raise ValueError("자료 없음")
            return validate(rows)
        if not items or len(rows) > expected:
            raise ValueError("수집 건수 불일치")
        previous = items
    raise ValueError("페이지 한도 초과")


def write_json(path, value):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=1), encoding="utf-8")
    temp.replace(path)


def main():
    OUT.mkdir(exist_ok=True)
    now = datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")
    status = {"확인한 때": now, "출처": SOURCE, "운영지역목록반영": False}
    try:
        key = os.environ.get("DATA_GO_KR_KEY", "").strip()
        if not key:
            raise ValueError("인증키 미설정")
        rows = collect(key)
        write_json(OUT / "regions-source.json", {"수집한 때": now, "출처": SOURCE, "건수": len(rows), "목록": rows})
        status.update({"상태": "수집·구조검사 성공", "건수": len(rows),
                       "후속검증": "시도·시군구 계층과 폐지·변경 반영 여부 대조 후 선택화면 연결"})
        result = 0
    except Exception as exc:
        # Never persist exception text: it may contain the authenticated URL.
        status.update({"상태": "미확인", "이유": "원본 수집 또는 구조 검사 실패",
                       "오류종류": type(exc).__name__,
                       "다음확인": "서비스 활용승인·인증·공식 응답 형식 확인. 기존 원본 유지"})
        result = 1
    write_json(OUT / "regions-status.json", status)
    print(json.dumps(status, ensure_ascii=False))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
