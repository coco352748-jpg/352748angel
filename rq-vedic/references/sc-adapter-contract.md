# SC·SC7·SC8 물리 사본과 Source Adapter 계약

## 1. 배치

마스터는 `$rq-vedic`에 둔다. 다음 세 파일을 SC, SC7, SC8의 각 `references/`에 물리적으로 복제한다.

- `sc-vedic-protocol-core.md`
- `19-layer-agent-map.json`
- `output-contract.md`

각 실행자는 자기 폴더의 로컬 사본을 읽는다. 런타임 상속이나 특정 Source 번호의 암묵 연결에 의존하지 않는다.

## 2. 사본 동일성

세 코어 사본은 마스터와 byte-identical이어야 한다. 다음을 실행해 검산한다.

```bash
python3 scripts/verify_sc_protocol_copies.py
```

하나라도 없거나 hash가 다르면 `SC_VEDIC_COPY_PARITY=HOLD`다. 완료를 선언하지 말고 어떤 사본이 다른지만 보고한다.

## 3. SC Root

SC Root는 사용자가 지정한 Source provider를 선택한다.

- SC7 지정: SC7 lane 하나
- SC8 또는 SC8 Source code 지정: SC8 lane 하나
- 둘 다 지정: 독립 lane 두 개
- 미지정 기본 `$rq-sc`: 기존 호환계약대로 SC7

Root는 Source를 받은 뒤 로컬 Vedic 코어와 agent map을 적용하고, 구조·19층 해석·문장 상태를 분리한다.

## 4. SC7 로컬 adapter

SC7 단독 호출은 Plain Source 공급만 한다. `$rq-sc` 또는 `$rq-sc7 + $rq-vedic`에서만 로컬 해석 사본을 활성화한다.

SC7의 archive/member hash, locator, direct/derived 상태, HOLD를 보존한다. Source Binding PASS·개인차트 240 PASS·Timing Gate CALCULATED를 해석 PASS로 승격하지 않는다.

`SOURCE_LANE_ID=SC7:<source_set_id>:<packet_hash>`

## 5. SC8 로컬 adapter

SC8 단독 호출은 명시된 Source layer만 공급한다. `$rq-sc` 또는 `$rq-sc8 + $rq-vedic`에서만 로컬 해석 사본을 활성화한다.

호출된 Source code·폴더·파일·member만 사용한다. 인접 family를 자동 병합하지 않고 원래 파일명·본문·direct-value registry를 보존한다.

`SOURCE_LANE_ID=SC8:<SOURCE_CODE>:<source_identity>`

## 6. 두 lane의 비교

SC7과 SC8을 함께 사용해도 서로의 공백·HOLD를 조용히 보충하지 않는다. 사용자 승인 교차검산에서만 `MATCH`, `DIFFERENCE`, `CONFLICT`, `NOT_COMPARABLE`로 비교한다. Source 원값은 통합하지 않는다.
