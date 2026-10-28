-- 효자 의료정보 신뢰관리 시스템: PostgreSQL 스키마 초안
-- 시험 설계 전용. 운영 DB에 적용하지 않음.
CREATE TABLE medical_facility (
  facility_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  facility_type TEXT NOT NULL CHECK (facility_type IN ('hospital','clinic','emergency','pharmacy')),
  region_code TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE facility_external_id (
  facility_id BIGINT NOT NULL REFERENCES medical_facility(facility_id),
  source_system TEXT NOT NULL,
  external_id TEXT NOT NULL,
  PRIMARY KEY (source_system, external_id),
  UNIQUE (facility_id, source_system, external_id)
);
CREATE TABLE source_snapshot (
  snapshot_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source_system TEXT NOT NULL,
  source_url TEXT NOT NULL,
  reference_date DATE,
  fetched_at TIMESTAMPTZ NOT NULL,
  sha256 CHAR(64) NOT NULL,
  raw_object_path TEXT NOT NULL,
  import_status TEXT NOT NULL CHECK (import_status IN ('staged','rejected','parsed')),
  CHECK (source_url LIKE 'https://%')
);
CREATE TABLE facility_observation (
  observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  facility_id BIGINT REFERENCES medical_facility(facility_id),
  snapshot_id BIGINT NOT NULL REFERENCES source_snapshot(snapshot_id),
  source_record_id TEXT,
  name TEXT,
  road_address TEXT,
  latitude NUMERIC(10,7),
  longitude NUMERIC(10,7),
  phone TEXT,
  license_status TEXT,
  hours_raw TEXT,
  observed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE verification_case (
  case_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  facility_id BIGINT NOT NULL REFERENCES medical_facility(facility_id),
  field_name TEXT NOT NULL,
  verdict TEXT NOT NULL CHECK (verdict IN ('unknown','verified','conflict','review_required','closed_or_suspended')),
  evidence_observation_id BIGINT REFERENCES facility_observation(observation_id),
  evidence_date DATE,
  reviewed_by TEXT,
  reviewed_at TIMESTAMPTZ,
  note TEXT,
  CHECK (verdict <> 'verified' OR (evidence_observation_id IS NOT NULL AND evidence_date IS NOT NULL))
);
CREATE TABLE publication_batch (
  publication_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  region_code TEXT NOT NULL,
  snapshot_sha256 CHAR(64) NOT NULL,
  approved_by TEXT NOT NULL,
  approved_at TIMESTAMPTZ NOT NULL,
  published_at TIMESTAMPTZ,
  rollback_of BIGINT REFERENCES publication_batch(publication_id)
);
-- 원본 observation은 append-only 정책을 별도 권한/트리거로 구현해야 함.
-- 공개 대상은 승인된 배치에서만 생성하며 위 테이블 자체를 앱에 노출하지 않음.
