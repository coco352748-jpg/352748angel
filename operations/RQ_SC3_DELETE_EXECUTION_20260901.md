# RQ SC3 중앙 영구삭제 실행 기록

```text
EXECUTION_ID=RQ_SC3_DELETE_20260901
UTC_CHECKED_AT=2026-09-01T15:59:53Z
TARGET=rq-sc3_EXTERNAL_PERSONAL_SKILL
PRESERVE=rq-vedic_INTERNAL_SC3
STATUS=HOLD_BACKEND_HTTP_500_CONFIRMED
PRE_PUSH_CHECK=PASS
MUTATION_CONFIRMED=false
SLOT_DELTA=0
OTHER_SKILLS_CHANGED=false
```

## 결과

외부 독립 `rq-sc3` 영구삭제 요청은 중앙 저장 서비스의 HTTP 500으로 반영되지 않았다. 성공 응답으로 오인하지 않고 원격 정본을 다시 조회했으며 삭제 대상의 4개 파일이 모두 그대로 존재했다.

동일 요청 반복은 중단했다. 영구삭제 단계 이후의 슬롯 회수 완료 판정은 하지 않는다.

## 삭제 대상 잠금

```text
TARGET_PACKAGE=skill-6a85c03a35a48191bfeee5d7a47fe71b
TARGET_FILE_COUNT_BEFORE=4
TARGET_FILE_COUNT_AFTER=4
DELETE_PACKET_FINGERPRINT=84a80e35f0f7677ca51cc5756d2fe0c562fd426c
CENTRAL_BASE_FINGERPRINT=268e698e077fc83021066ffba9d4cb8145ffa076
```

삭제 패킷에는 다음 4개 파일의 삭제만 포함된다.

- `SKILL.md`
- `agents/openai.yaml`
- `assets/icon.svg`
- `references/DDOMAIN__FN.txt`

다른 스킬 파일은 포함되지 않는다.

## Vedic 내부 보존 검산

```text
INTERNAL_ROOT=skill-6a849cb75c7c8191b06a140602637335/internal/sc-series/sc3
OWNER_CONTRACT_PRESENT=true
DDOMAIN_SOURCE_PRESENT=true
DDOMAIN_SHA256=9e002b7d774cf17dbf533886acd3b2841fd0518c4b868017f07b562a30e17622
EXTERNAL_OWNER_REQUIRED=false
COMPACT_CALL=$rq-vedic-sc3
INTERNAL_ROUTE_STATUS=PASS
```

현재 Vedic registry는 SC3 selector를 내부 `owner-contract.md`로 연결한다. 외부 `rq-sc3`가 없어도 작동하도록 `external_owner_required=false`가 잠겨 있다.

## 중앙 응답

네 가지 제출 경로를 구분해 확인했다.

1. 중앙 기본 정본 직접 반영 요청
2. 준비된 영구삭제 작업 단위 제출
3. 원래 제출 검문 상태 재확인 뒤 작업 단위 재제출
4. 실행 가능한 별도 검문 경로에서 LFS 사전검문 PASS 뒤 작업 단위 제출

네 요청 모두 동일하게 다음 응답으로 종료됐다.

```text
error=RPC failed
http_status=500
transport_message=remote end hung up unexpectedly
pre_push_check=PASS
central_state_changed=false
```

성공처럼 보일 수 있는 `Everything up-to-date` 문구가 함께 나왔으나 이후 중앙 정본을 재조회한 결과 대상이 남아 있으므로 성공 증거로 사용하지 않는다.

## 최종 판정

```text
TARGET_LOCK=PASS
PROTECTED_COPY_LOCK=PASS
HASH_CHECK=PASS
DELETE_PACKET_SCOPE=PASS
CENTRAL_DELETE=HOLD_BACKEND_HTTP_500
REMOTE_ABSENCE_VERIFY=FAIL
SLOT_RECOVERY=NOT_ACHIEVED
OTHER_SKILLS=UNCHANGED
```

## 다음 실행점

중앙 저장 서비스의 쓰기 경로가 복구되면 기존 삭제 패킷을 그대로 한 번 제출한다. 새 양식을 만들거나 삭제 대상·보존 대상을 다시 선정하지 않는다.

반영 후 다음을 모두 재검증한다.

1. 외부 대상 4개 파일이 중앙 정본에서 0개가 됨
2. 슬롯 수가 정확히 1 감소함
3. Vedic 내부 SC3 Source hash가 유지됨
4. `$rq-vedic-sc3` 내부 호출이 PASS함
5. 다른 스킬 변화가 없음


## 최종 병목 확인

원래 검문 훅이 실행 불가한 마운트에 있던 문제를 분리해, 동일 훅을 실행 가능한 경로에서 직접 PASS시킨 뒤 제출했다. 그 상태에서도 중앙이 같은 HTTP 500을 반환했고 정본은 변하지 않았다.

따라서 현재 실패 원인은 삭제 패킷·대상 식별·Vedic 내부 보존·로컬 사전검문이 아니라 중앙 저장 서비스의 쓰기 처리다. 이 실행에서는 더 이상 제출하지 않는다.
