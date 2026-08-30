---
name: rq-sc8
description: RQ PIKACHU 20D의 SC 실제값 정본과 번호별 Source 하위폴더를 공급하는 라우터. 사용자가 $rq-sc8 또는 $rq-sc8-1ab, $rq-sc8-2ab, $rq-sc8-3ab, $rq-sc8-4ab, $rq-sc8-4ak, $rq-sc8-5a, $rq-sc8-5ab, $rq-sc8-6ab, $rq-sc8-7ab, $rq-sc8-8ab, $rq-sc8-9ab, $rq-sc8-10ab, $rq-sc8-12ab, $rq-sc8-13ab, $rq-sc8-14ab, $rq-sc8-16ab, $rq-sc8-17ab, $rq-sc8-18ab, $rq-sc8-19ab, $rq-sc8-20ab, $rq-sc8-21ab를 호출하거나 SC8의 특정 Source 계층·ZIP·20D member를 요청할 때 사용한다. 단독 호출은 지정 Source만 공급하며, $rq-sc 또는 $rq-sc8+$rq-vedic 조합에서는 SC8 내부의 물리 복제된 Vedic 코어로 19층×ELIVEDIC·ELICOLLEGE·ELIPHD 해석을 실행할 수 있다. 호출된 계층만 읽고 인접 패밀리를 자동 병합하지 않는다.
---

# RQ SC8

## 실행 잠금

- `TARGET_SCOPE=SC8_CANONICAL_AND_SOURCE_LAYER_ROUTER`
- `PARENT_CALL=$rq-sc8`
- `LAYER_CALL=$rq-sc8-<SOURCE_CODE>`
- `VALIDATION=EXPLICIT_USER_REQUEST_ONLY`
- `AUTO_MERGE=PROHIBITED`
- `SOURCE_FILENAME_MUTATION=PROHIBITED`
- `INFORMATION_LOSS=0`
- `LOCAL_VEDIC_COPY=AVAILABLE_DORMANT_UNTIL_EXPLICIT_INTERPRETATION_MODE`

일반 호출에서는 검증기를 실행하지 않는다. 사용자가 검증을 명시적으로 요청할 때만
`scripts/pikachu_sc8.py`를 사용한다.

## 호출 절차

1. 현재 호출키를 먼저 잠근다.
2. `$rq-sc8` 단독 호출이면 부모 라우터만 활성화한다.
3. `$rq-sc8-<SOURCE_CODE>` 호출이면 `references/sc8-layer-folders.json`에서 정확한 폴더를 찾는다.
4. 해당 폴더 안의 Source만 공급한다. 다른 번호·패밀리를 자동 호출하거나 합치지 않는다.
5. 한 호출키 아래 Source가 여러 개면 사용자가 지정한 Target과 일치하는 파일만 고른다.
   Target이 없고 선택에 따라 결과가 달라지면 `HOLD`하고 필요한 구분만 요청한다.
6. Source의 원래 파일명·대소문자·확장자·본문을 변경하지 않는다.
7. `$rq-sc` 또는 `$rq-sc8 + $rq-vedic` 해석 모드이면 `references/sc-vedic-protocol-core.md`, `references/19-layer-agent-map.json`, `references/output-contract.md`, `references/sc-vedic-local-adapter.md`를 전부 읽는다.
8. SC8 단독 Source 호출에서는 로컬 Vedic 사본과 57개 해석 에이전트를 실행하지 않는다.

## 폴더 규칙

실제 폴더명은 셸과 스킬 이름 규칙에 맞춰 소문자로 저장한다. `$`는 호출할 때만 붙인다.

- 호출키: `$rq-sc8-1ab`
- 실제 폴더: `assets/source-layers/rq-sc8-1ab/`

같은 Source code를 공유하는 파일은 같은 번호 폴더 안에 함께 보존한다. 세부 Source의
권한과 역할은 합치지 않는다.

사용자 교정에 따라 `$rq-sc8-5a`에는 Spirit Chalit·Moon·Pushkara Bhaga·Upagraha를
배치하고, `$rq-sc8-5ab`에는 Bhava Bala·Bhava Aspect만 배치한다.

`$rq-sc8-20ab`는 Yoga Source만, `$rq-sc8-21ab`는 Transit Source만 공급한다.
Yoga와 Transit은 서로 다른 해석층이며 자동 병합하지 않는다.

## 정본 자산

- PIKACHU 20D 정본: `assets/pikachu-sc-canonical/`
- 번호별 Source 폴더: `assets/source-layers/`
- 폴더 라우팅 정본: `references/sc8-layer-folders.json`
- 실제값 레지스트리: `references/pikachu-sc8-direct-values.json`
- Source 계약: `references/pikachu-sc8-manifest.json`

사용자가 특정 D차트나 member를 지정하지 않으면 임의로 하나를 대표값으로 선택하지 않는다.

## Vedic 로컬 사본 금지선

- SC8 단독 Source 호출에서 19층 해석 자동 실행 금지
- 인접 Source 번호·family를 Vedic layer map에 있다는 이유로 자동 호출 금지
- SC7 값으로 SC8 공백·HOLD를 조용히 보충 금지
- SC·SC7·SC8 로컬 코어의 버전·hash 불일치 상태에서 해석 PASS 선언 금지
