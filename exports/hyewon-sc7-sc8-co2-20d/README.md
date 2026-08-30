# HYEWON SC7 · SC8 04 공동장 20D Export

04 공동장(CoPresence / Vedic CO2) 층만 분리한 저장본이다.

## 구성

- `HYEWON_SC7_CO2_20D_SOURCE.zip`
  - `$rq-sc7`의 `vedic_co2` 원본 ZIP을 바이트 그대로 보존한 복사본
  - 원본명: `07_4AB_VeDic_CO2_Sc_.zip`
  - 20D member, 본문 수정 없음
- `HYEWON_SC8_CO2_PIKACHU_20D.zip`
  - `$rq-sc8` PIKACHU 정본 20개 ZIP에서 04 공동장 Applied member만 추출한 묶음
  - D1·D9은 `04_1A`, 나머지 Target D는 `04_1B`
- `SC7/`, `SC8/`
  - 위 두 ZIP의 펼친 20D 파일
- `templates/`
  - 사용자 첨부 템플릿 4개를 값 Source와 분리해 원문 그대로 보존
- `HYEWON_SC7_SC8_CO2_20D_BUNDLE.zip`
  - SC7·SC8·템플릿·manifest 전체 묶음

## 활성 D 순서

`D1, D9, D2, D3, D4, D5, D6, D7, D8, D10, D11, D12, D16, D20, D24, D27, D30, D40, D45, D60`

`D50`은 `VOID`이며 포함하지 않는다.

## 보존 경계

- 03번 `CO2 First Integration`과 혼합하지 않음
- OCR 재실행 없음
- 공동장 값 계산·보충·해석 없음
- SC7과 SC8 상호 덮어쓰기 없음
- 원문 파일명·대소문자·본문 바이트 수정 없음
- 첨부 템플릿 적용·치환 없음

세부 해시와 크기는 `CO2_EXPORT_MANIFEST.json`에 기록했다.
