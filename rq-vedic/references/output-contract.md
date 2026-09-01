# RQ Vedic 출력·인계 계약

## 목차

1. 전체 패킷
2. 층별 에이전트 계약
3. Rashi–Bhava 3층 필수검산
4. 차트 잠금과 학자 후속층
5. 상태와 최종 출력

## 1. 전체 패킷

내부 결과를 다음 구조로 유지하라.

```json
{
  "protocol_id": "RQ_VEDIC_19_LAYER_V1",
  "chart_input_lock": {},
  "layers": [],
  "chart_native_lock": {},
  "scholar_overlay": {},
  "qa": {}
}
```

`chart_input_lock`에는 최소한 `status`, `target`, `source_lanes`, `input_refs`, `unknowns`, `conflicts`, `calculation_settings`를 둬라. `source_lanes`에는 `chart_source`와 `domain_coordinate`를 분리해 기록하고, 각 lane의 `source_lane_id`, `source_ref`, `status`, `authority_boundary`를 보존하라. 특정 차트 Source 번호를 기본값으로 만들지 말고, SC3 좌표를 차트 실값으로 승격하지 마라.

## 2. 층별 에이전트 계약

각 층 객체에 다음을 둬라.

```text
layer_id
status=PASS|HOLD|NOT_APPLICABLE|CONFLICT
method_admission
source_boundary
agents.ELIVEDIC
agents.ELICOLLEGE
agents.ELIPHD
handoff
```

### ELIVEDIC

필수 필드:

- `agent_id`
- `input_refs`
- `observations`
- `boundaries`
- `unknowns`
- `output_ref`

관찰과 입력 경계만 기록하라. 해석문·인과·최종귀속을 만들지 마라.

### ELICOLLEGE

필수 필드:

- `agent_id`
- `input_ref`
- `input_refs`
- `pattern_candidates`
- `supporting_observations`
- `contrasts`
- `exceptions`
- `structured_interpretation`
- `output_ref`

ELIVEDIC 관찰 밖의 값을 넣지 마라. 패턴 후보와 예외검사를 함께 적고 최종 인과로 승격하지 마라.

### ELIPHD

필수 필드:

- `agent_id`
- `input_ref`
- `input_refs`
- `deep_structure`
- `causal_joints`
- `counterfactual_limits`
- `attribution`
- `recovery`
- `residual_uncertainty`
- `final_layer_interpretation`
- `output_ref`

입력과 층간 관절이 닫히지 않은 후보를 최종 주장으로 승급하지 마라. 인과표현을 쓰면 대안 설명과 반사실 한계를 함께 적어라.

### Handoff

`handoff`에는 `from_layer`, `to_layer`, `passed_refs`, `unresolved`, `blocked_claims`를 둬라. 앞 층의 원값을 복사해 수정하지 말고 참조 ID로 넘겨라.

## 3. Rashi–Bhava 3층 필수검산

3층에 다음 boolean을 모두 두고 모두 `true`가 아니면 `PASS`를 금지하라.

```json
{
  "boundary_checks": {
    "rashi_raw_preserved": true,
    "bhava_raw_preserved": true,
    "planet_not_deleted": true,
    "degree_conflict_propagated": true,
    "full_packet_before_role_filter": true
  }
}
```

`moved_out`, `탈락`, `생존자만 full packet` 같은 삭제상태를 사용하지 마라. 제외할 수 있는 것은 현재 Target Bhava에서 입력근거가 없는 직접점유 역할뿐이다.

## 4. 차트 잠금과 학자 후속층

`chart_native_lock`에는 `status`, `input_trace_complete`, `method_trace_complete`, `unresolved`, `locked_interpretation_ref`를 둬라.

`scholar_overlay.status`는 다음 중 하나다.

- `NOT_REQUESTED`
- `NOT_APPLICABLE`
- `HOLD`
- `APPLIED`

`APPLIED`는 `chart_native_lock.status=PASS`일 때만 허용하라. 이때 `scholars`, `technical_source_refs`, `comparisons`, `conflicts`, `base_lock_reopened`를 기록하라. `base_lock_reopened`는 사용자 승인 없이는 반드시 `false`다.

P.V.R. Narasimha Rao와 Sanjay Rath를 선호하되, Sanjay Rath의 영성·종교·의례·remedy 내용은 넣지 마라. 정확한 기술자료가 없으면 저자 이름만으로 규칙을 만들지 마라.

## 5. 상태와 최종 출력

검산 상태는 `PASS`, `REVISE`, `HOLD`, `CONFLICT` 중 하나로 반환하라. 미해결 방법·입력이 최종 결론에 필요한 경우 `PASS`를 금지하라.

사용자에게 기본적으로 다음만 보여라.

1. 차트 자체 결론
2. 결론을 만든 핵심 층·입력 경로
3. `CURRENT_COMMON_CORE`와 `METHOD_SPECIFIC`의 구분
4. HOLD·CONFLICT·반례·한계
5. 별도 요청 시에만 학자 후속 비교

57개 내부 에이전트 패킷 전체는 사용자가 요구하거나 감사·검산에 필요할 때만 펼쳐라.
