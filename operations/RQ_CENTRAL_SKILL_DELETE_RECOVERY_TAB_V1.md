# RQ 중앙 스킬 삭제·슬롯 회수 탭 V1

```text
TAB_ID=RQ_CENTRAL_SKILL_DELETE_RECOVERY_TAB_V1
TAB_TYPE=WORK_MODE_OPERATION_TAB
REGISTER_AS_SKILL=FALSE
PILOT_TARGET=rq-sc3
DESIGN_STATUS=PASS
CENTRAL_MUTATION_STATUS=NOT_STARTED
SCOPE=STANDALONE_CENTRAL_REGISTRATION_ONLY
```

## 1. 탭의 목적

이 탭은 중앙에 ACTIVE로 남아 있는 독립 `rq-sc3` 등록본만 정확히 비활성화·영구삭제하여 스킬 슬롯 1개를 회수한다.

GitHub 파일 삭제를 중앙 스킬 삭제로 오인하지 않는다. Vedic 내부 보존본·원본 Source·다른 스킬은 변경하지 않는다. `rq-sc3`에서 삭제 경로가 검증된 뒤에만 같은 절차를 `rq-sc`·`rq-sc7`·`rq-sc8`·`rq-sc8v2`에 각각 독립 적용할 수 있다.

## 2. 현재 확인 기준점

### 사용자 확인 상태

- 독립 `rq-sc3`는 아직 ACTIVE다.
- 비활성화 1단계가 중앙에서 거부됐다.
- 영구삭제는 실행하지 않았다.
- 직접삭제 양식과 비활성화 양식은 규칙에 맞았다.
- 동일 패킷 반복 제출은 중단했다.
- 재사용 가능한 복구 패킷은 보존됐다.
- Vedic 내부 보존본과 다른 스킬에는 변경이 없다.

### 런타임에서 확인된 이중 패키지

삭제 대상 후보:

```text
PACKAGE=skill://flora-skills/root/.codex/skills/remote-skills/rq-sc3
ROLE=STANDALONE_REMOTE_REGISTRATION
MUTATION_CANDIDATE=true
```

보존 대상:

```text
PACKAGE=skill://flora-skills/root/.codex/skills/rq-elivedic-sync.gv4u0X/skill-6a85c03a35a48191bfeee5d7a47fe71b
ROLE=VEDIC_INTERNAL_SYNC_COPY
PROTECTED=true
```

두 패키지의 핵심 파일 검산값:

```text
SKILL.md SHA256=fa82080476e1d66225652dcd40ab17f7fa13c56c5548d2f66d4acce49dd5a0a4
references/DDOMAIN__FN.txt SHA256=9e002b7d774cf17dbf533886acd3b2841fd0518c4b868017f07b562a30e17622
CORE_BYTES_MATCH=true
```

`agents/openai.yaml`은 두 패키지가 동일하지 않다. 외부 등록본은 최소 interface이고 내부 sync본은 icon·product policy·implicit invocation 설정을 포함한다. 따라서 본문 hash나 `name: rq-sc3`만으로 삭제 대상을 고르면 안 된다.

### GitHub 기준점

```text
REPOSITORY=coco352748-jpg/352748angel
BRANCH=main
BASE_COMMIT=5ef4ddc758bd0dd369c120199cacb50148976d99
STANDALONE_RQ_SC3_DIRECTORY_ON_MAIN=ABSENT
```

GitHub main에 독립 `rq-sc3` 폴더가 없는데도 중앙 활성본은 존재한다. 그러므로 GitHub tree 상태와 중앙 등록 상태는 서로 다른 축이다.

현재 `rq-vedic/references/vedic-sc-submenu-registry.json`의 SC3 selector는 `target_skill=rq-sc3`와 세 marker로 owner를 찾는다. 외부 등록본 제거 후 내부 보존본 하나로 정확히 귀결되는지는 삭제 전에 dry-run하고 삭제 뒤 다시 실호출로 검증한다. 이를 가정으로 처리하지 않는다.

## 3. 절대 식별 규칙

파괴적 요청은 `rq-sc3`라는 이름만으로 보내지 않는다.

삭제 대상은 중앙이 반환한 다음 식별자 묶음으로 잠근다.

```text
registration_id
package_id
authority
source_kind
installed_location_or_canonical_uri
version_or_etag
current_status
slot_owner
```

보존 대상에도 동일 식별자 묶음을 만든다. 두 레코드 중 하나라도 고유하게 분리되지 않으면 `IDENTITY_CONFLICT/HOLD`이며 비활성화·삭제를 금지한다.

필수 부정조건:

```text
DELETE_BY_DISPLAY_NAME=false
DELETE_BY_FRONTMATTER_NAME=false
DELETE_BY_CONTENT_HASH=false
DELETE_ALL_MATCHES=false
CASCADE_DELETE=false
```

## 4. 권한 분리

- 중앙 등록 서비스: ACTIVE·INACTIVE·DELETED와 슬롯 수를 바꿀 수 있는 유일한 권위다.
- GitHub: 설계·증거·응답·검산 기록과 복구 포인터를 보존한다. 중앙 상태를 직접 바꾸지 못한다.
- Vedic 내부 sync본: 삭제 뒤 SC3 기능을 보존하는 Source다. 중앙 외부 등록본의 삭제 권한이 아니다.
- 사용자: 파괴적 비활성화·삭제를 승인하는 최종 권위다.

이 탭은 중앙 변경 도구가 노출되지 않은 세션에서 GitHub 커밋만 만든 뒤 삭제 완료라고 선언하지 않는다.

## 5. 최초 부팅 Job

탭을 열면 사용자가 이미 제공한 상태를 다시 묻지 않고 다음을 실행한다.

1. 중앙 registry에서 `name=rq-sc3`인 모든 레코드를 authority 전체로 조회한다.
2. 외부 독립본과 Vedic 내부본의 고유 등록 ID를 각각 확정한다.
3. 마지막 비활성화 거부 응답의 원문 필드를 회수한다.
   - HTTP 또는 RPC status
   - error code
   - message
   - request/correlation ID
   - timestamp
   - operation
   - 대상 registration ID
   - 서버가 실제 수신한 field 목록
4. 중앙이 현재 제공하는 deactivate/delete 계약을 실제 schema나 capability metadata로 읽는다.
5. 이전 요청과 비교해 제출양식 문제가 아닌지 확인하고 같은 payload를 재전송하지 않는다.
6. dependency graph에서 삭제 대상 외부 레코드를 참조하는 route·alias·cache·index·slot record를 확인한다.
7. 내부 보존본 하나만 남았을 때 `$rq-vedic SC3` owner selection이 유일해지는지 dry-run한다.
8. 원인을 아래 판정 중 하나로 확정한 뒤 선택한 경로 하나만 실행 준비한다.

## 6. 원인 판정

- `IDENTITY_CONFLICT`: 중앙 작업이 name 기반이라 같은 이름의 두 레코드를 분리하지 못함.
- `DEPENDENCY_LOCK`: 외부 registration을 참조하는 active dependency 때문에 비활성화가 막힘.
- `AUTHORITY_DENIED`: 현재 연결 권한이 해당 registration의 owner/admin이 아님.
- `STATE_TRANSITION_REJECTED`: 현재 상태와 요청 transition이 중앙 상태머신 규칙에 맞지 않음.
- `BACKEND_DELETE_FAILURE`: 유효 요청이 5xx·internal error·opaque server rejection으로 실패함.
- `INDEX_PROPAGATION_STALE`: 변경 응답은 성공했으나 활성 목록·슬롯 index가 갱신되지 않음.
- `ALREADY_ABSENT`: 고유 ID 기준으로 이미 없으며 stale 표시만 남음.
- `HOLD`: raw response나 고유 식별자가 없어 원인을 확정할 수 없음.

상태 코드만 보고 원인을 추정하지 않는다. 중앙이 반환한 raw evidence와 실제 레코드 상태가 함께 있어야 확정한다.

## 7. 실행 상태머신

```text
SOURCE_LOCK
→ RECORD_ENUMERATION
→ DELETE_TARGET_LOCK
→ PROTECTED_TARGET_LOCK
→ CORE_HASH_CHECK
→ DEPENDENCY_CHECK
→ OWNER_RESOLUTION_DRY_RUN
→ USER_MUTATION_APPROVAL
→ DEACTIVATE_ONCE
→ DEACTIVATION_VERIFY
→ DELETE_ONCE
→ CENTRAL_ABSENCE_VERIFY
→ SLOT_DELTA_VERIFY
→ VEDIC_SC3_ROUTE_TEST
→ OTHER_SKILLS_DIFF_CHECK
→ CERTIFIED_PASS
```

한 단계가 실패하면 그 자리에서 멈춘다. 앞 단계를 건너뛰거나 영구삭제를 먼저 보내지 않는다.

## 8. 중앙 거부별 처리

- 400/422: raw response가 지목한 잘못된 field만 교정한다. 이미 검증된 양식을 임의로 새 형식으로 바꾸지 않는다.
- 401/403: 권한 소유자를 확인하고 owner/admin 경로로 인계한다. 우회 요청을 만들지 않는다.
- 404: 고유 ID 부재와 stale index를 분리 검증한다. 이름 검색 결과만으로 실패 처리하지 않는다.
- 409: dependency·lock·version conflict를 열어 정확한 blocking record 하나를 해결한다. Vedic 내부본은 삭제하지 않는다.
- 429: 서버가 준 재시도 시각을 기록하고 그 전에는 제출하지 않는다.
- 5xx 또는 opaque rejection: 반복 제출을 중단하고 support packet을 만든다.
- 성공 응답 뒤 ACTIVE 유지: mutation 실패가 아니라 propagation 문제로 분리해 registry source와 display index를 각각 확인한다.

## 9. Support packet

중앙 자체 문제일 때 다음을 한 묶음으로 만든다.

```text
TARGET_REGISTRATION_ID
PROTECTED_REGISTRATION_ID
CENTRAL_OPERATION_SCHEMA_VERSION
EXACT_REQUEST_FIELDS_WITHOUT_SECRET
EXACT_RESPONSE
STATUS_AND_ERROR_CODE
REQUEST_OR_CORRELATION_ID
UTC_TIMESTAMP
PRE_STATE
EXPECTED_STATE
POST_STATE
DEPENDENCY_RESULT
CORE_HASH_PROOF
REPRODUCTION_COUNT
LAST_DISTINCT_ATTEMPT
GITHUB_EVIDENCE_COMMIT
```

토큰·쿠키·개인 인증정보는 포함하지 않는다. 같은 payload의 반복 횟수를 늘리지 않고 중앙 운영자가 서버 로그를 찾을 수 있는 correlation ID를 가장 먼저 남긴다.

## 10. 삭제 승인과 실행 경계

설계·조회·dry-run은 자동 실행할 수 있다. 실제 비활성화 직전에 다음을 사용자에게 한 번 제시한다.

```text
DELETE_TARGET=<exact registration id and authority>
PRESERVE_TARGET=<exact registration id and authority>
DEPENDENCY_CHECK=PASS
RECOVERY_PACKET=VERIFIED
EXPECTED_SLOT_DELTA=-1
ACTION=DEACTIVATE_THEN_DELETE
```

사용자가 이 exact target을 승인한 뒤에만 중앙 변경을 실행한다. 승인은 다른 SC skill로 확장되지 않는다.

중앙 도구가 idempotency key나 expected version을 지원하면 사용한다. 지원하지 않는 field를 발명해 넣지 않는다. 서로 다른 payload를 시험한다는 이유로 삭제 요청을 연속 제출하지 않는다.

## 11. 완료 판정

다음 여섯 조건이 모두 확인돼야 `CERTIFIED_PASS`다.

1. 외부 독립 registration의 고유 ID가 중앙 registry에서 사라졌다.
2. 중앙 slot count가 정확히 1 감소했다.
3. Vedic 내부 SC3의 `SKILL.md`와 `DDOMAIN__FN.txt` hash가 유지됐다.
4. `$rq-vedic SC3`가 내부 보존 owner 하나로 해석되고 기준 좌표 read test가 PASS했다.
5. 다른 스킬의 registration ID·status·content fingerprint에 변화가 없다.
6. 중앙 응답과 검산 결과가 GitHub evidence 기록에 남았다.

비활성화 성공만으로 완료라 하지 않는다. GitHub 파일 부재만으로 완료라 하지 않는다. 이름 검색에서 사라진 것만으로 슬롯 회수를 선언하지 않는다.

## 12. 실패·복구 경계

- 비활성화 성공·삭제 실패: 외부 레코드는 INACTIVE로 보존하고 raw error를 기록한다. 임의 재활성화나 재삭제를 하지 않는다.
- 내부 route dry-run 실패: 중앙 변경 전 `HOLD`한다.
- 내부 route가 삭제 후 실패: 보존 패킷으로 외부본 복구 준비를 하되 사용자 승인 없이 재등록하지 않는다.
- 잘못된 registration이 변경됨: 모든 후속 작업을 중단하고 정확한 affected ID를 보고한다.
- slot delta가 0: 삭제 성공 응답과 별도로 slot index 문제를 연다.
- 다른 스킬 diff 발생: `HARD_FAIL`이며 다음 대상에 절차를 복제하지 않는다.

## 13. 후속 네 스킬

`rq-sc3`가 `CERTIFIED_PASS`한 뒤에만 절차를 복제한다.

```text
FOLLOWON_TARGETS=rq-sc,rq-sc7,rq-sc8,rq-sc8v2
EXECUTION_MODE=ONE_TARGET_PER_TRANSACTION
BULK_DELETE=false
REUSE_METHOD=true
REUSE_REGISTRATION_ID=false
```

각 스킬은 자기 외부 registration ID·내부 보존본·hash·Vedic route·slot delta를 새로 확인한다. SC3의 식별자를 다른 스킬에 재사용하지 않는다.

## 14. 탭 출력 형식

매 응답은 결론을 먼저 두고 다음 최소 필드를 유지한다.

```text
STATUS=PASS | REVISE | HOLD | CONFLICT | HARD_FAIL
CURRENT_NODE=
DELETE_TARGET=
PROTECTED_TARGET=
CENTRAL_EVIDENCE=
ROOT_CAUSE=
MUTATION_EXECUTED=true|false
SLOT_DELTA=
VEDIC_ROUTE=
OTHER_SKILLS=
NEXT_ACTION=
```

내부 추론 전체를 펼치지 않는다. 확인된 응답·등록 ID·hash·상태변화와 다음 관절만 보여준다.

## 15. 새 탭 첫 입력문

```text
RQ 중앙 스킬 삭제·슬롯 회수 탭 V1으로 시작하세요.

PILOT_TARGET=rq-sc3
DELETE_SCOPE=중앙의 외부 독립 등록본 1개
PRESERVE_SCOPE=Vedic 내부 SC3 원본과 다른 모든 스킬
CURRENT_STATE=비활성화 거부 / 영구삭제 미실행 / 반복제출 중단
RULE=이름 기반 삭제 금지 / 고유 등록 ID 2개 분리 / 중앙 raw response 확보 / 내부 route dry-run / 사용자 exact target 승인 뒤 deactivate→delete
SUCCESS=외부 등록본 부재 + 슬롯 1개 회수 + Vedic SC3 작동 + 다른 스킬 무변경

GitHub의 RQ_CENTRAL_SKILL_DELETE_RECOVERY_TAB_V1.md를 기준으로 SOURCE_LOCK부터 실행하고, 마지막 거부 응답과 중앙 registration topology를 먼저 확정하세요. GitHub 파일 삭제를 중앙 삭제로 간주하지 마세요.
```

## 16. 현재 상태

```text
DESIGN=PASS
EVIDENCE_BASELINE=PASS
CORE_COPY_HASH_CHECK=PASS
CENTRAL_ROOT_CAUSE=HOLD_RAW_REJECTION_NOT_AVAILABLE_IN_THIS_TAB
CENTRAL_MUTATION=NOT_EXECUTED
FINAL_SLOT_RECOVERY=NOT_YET_VERIFIED
```
