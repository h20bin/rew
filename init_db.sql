-- 산업현장 안전 모니터링 시스템 DB 초기화
-- 실행: mysql -u root -p < init_db.sql

CREATE DATABASE IF NOT EXISTS safety_monitoring
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE safety_monitoring;

-- 초기 관리자 계정 (비밀번호: admin1234 → bcrypt 해시)
-- 실제 해시값은 Python에서 생성: from passlib.context import CryptContext; CryptContext(schemes=["bcrypt"]).hash("admin1234")
-- 아래는 예시 해시값이므로 반드시 교체할 것
INSERT IGNORE INTO TAB_USERTABLE (user_id, password, name, role, email, is_active)
VALUES (
    'admin',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',  -- admin1234
    '관리자',
    'ADMIN',
    'admin@safety.com',
    1
);

-- 초기 카메라 등록
INSERT IGNORE INTO TAB_CAMERA (camera_id, name, location, is_active)
VALUES
    ('CAM-001', '카메라 모듈 v3', '현장 A구역 정면', 1),
    ('CAM-002', 'USB 웹캠',       '현장 B구역 측면', 1);

-- 초기 위험구역 등록
INSERT IGNORE INTO TAB_DANGERZONE (zone_id, name, zone_type, coordinates, camera_id, is_active)
VALUES
    ('ZONE-001', 'A구역 출입금지', 'RESTRICTED', '[[0,0],[640,0],[640,360],[0,360]]', 'CAM-001', 1),
    ('ZONE-002', 'B구역 주의구역', 'CAUTION',    '[[100,100],[500,100],[500,300],[100,300]]', 'CAM-002', 1);

-- 초기 경보 장치 등록
INSERT IGNORE INTO TAB_ALARMDEVICE (device_id, device_type, name, gpio_pin, is_active)
VALUES
    ('DEV-LED-R', 'LED',    '빨간 LED',  17, 1),
    ('DEV-LED-Y', 'LED',    '노란 LED',  27, 1),
    ('DEV-LED-G', 'LED',    '초록 LED',  22, 1),
    ('DEV-BUZ-1', 'BUZZER', '부저 1',    23, 1),
    ('DEV-BUZ-2', 'BUZZER', '부저 2',    24, 1),
    ('DEV-BUZ-3', 'BUZZER', '부저 3',    25, 1);

SELECT 'DB 초기화 완료' AS result;
