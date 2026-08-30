# SC7 ↔ SC8 Rashi·Bhava 양방향 문법 역산

복원 호출키: `$rq-sc7-sc8-grammar`

## 판정

**현재 판정은 `HOLD`다. `600/600 완료`가 아니다.**

지정 브랜치의 두 ALL ZIP을 무수정으로 열어 계수한 결과, 실제 소스는 20D × 12H × 2 lane = **480 좌표**다. Rashi 240개와 Bhava 240개는 모두 존재하며, SC7 핵심 원자와 SC8 핵심 원자의 결속은 **480/480** 통과했다. 그러나 다음 두 조건 때문에 완전한 양방향 문서 컴파일러라고 선언할 수 없다.

1. 요청된 600개 중 120개에 해당하는 source/target 대응쌍이 제공된 ZIP에 없다.
2. 역사적 SC8 문서가 SC7의 모든 메타·노트·공백열을 담지 않으며, Bhava에는 SC7 입력 원자로 선택할 수 없는 장문/단문 두 직렬화 프로필이 섞여 있다.

실행기는 이 경계를 숨기지 않는다. 480개 핵심 IR을 추출·검증하지만, 전체 TXT를 정확히 결정할 수 없는 상태에서는 TXT를 만들지 않고 종료코드 2와 `HOLD` JSON을 반환한다. `--allow-hold`는 진단 파이프라인에서만 종료코드를 0으로 바꾸며 판정을 PASS로 바꾸지 않는다.

## Source 잠금

| 항목 | 잠금값 |
|---|---|
| Repository | `coco352748-jpg/352748angel` |
| Branch | `exports/sc7-sc8-rashi-bhava-20d` |
| Path | `exports/hyewon-sc7-sc8-rashi-bhava-20d/` |
| SC7 ALL ZIP SHA-256 | `b4bf526397aad3443eb7c4a883c866ed5a5ff7367341adf490aedff4ee4f427e` |
| SC8 ALL ZIP SHA-256 | `732ac5370fe9703027339db691883825c1be07d118b98342c3e5b1a9255b9f72` |
| 첨부 D1 Rashi 빈 템플릿 SHA-256 | `fcd97e8afe61fd84ab2529a760d52d7235b5a1eb2de7814b0fabff5840601c59` |
| 첨부 D1 Bhava 빈 템플릿 SHA-256 | `06024c59598f96027b1c9fe3575393347d9282a68db63a08f30b0b85c002e423` |

활성 D 순서는 다음으로 고정한다.

`D1, D9, D2, D3, D4, D5, D6, D7, D8, D10, D11, D12, D16, D20, D24, D27, D30, D40, D45, D60`

소스 파일 계수:

| Lane | D 문서 | House/D | 좌표 | SC7 누락 | SC8 누락 |
|---|---:|---:|---:|---:|---:|
| Rashi | 20 | 12 | 240 | 0 | 0 |
| Bhava | 20 | 12 | 240 | 0 | 0 |
| 합계 | 40 | — | 480 | 0 | 0 |
| 사용자 계약 | — | — | 600 | **120 미제공** | **120 미제공** |

첨부된 두 D1 파일은 2026-08-31 표기의 **신형 typed empty template**이며, ZIP 안의 2026-06-04 역사적 D1 Applied 문서를 단순히 값만 지운 파일이 아니다. 따라서 typed slot 사전과 lane 경계 확인에는 사용했지만, 역사적 Applied 문서의 byte skeleton으로 대체하지 않았다.

## 무손실 판정 기준

각 자료를 다음 원자 좌표로 분해한다.

`D → Lane(Rashi/Bhava) → House → Section → Block → Row → Field → Token`

컴파일러의 내부 IR은 다음 두 계층을 분리한다.

- **Source IR**: SC7에 실제로 보이는 값, 상태, 표기, 순서, 메타, 공백 정보.
- **Derived IR**: 두 lane을 덮어쓰지 않은 채 source 원자에서 기계적으로 만들어지는 order, gap, alignment status, 반복문 프레임.

어떤 derived field도 자신의 source anchor 목록을 가져야 한다. source anchor가 하나라도 없으면 `HOLD`다. 조티시 일반론이나 보이지 않는 값을 계산 source로 쓰지 않는다.

정확 PASS는 다음 네 식을 **UTF-8 파일 bytes** 수준에서 모두 만족할 때만 가능하다.

\[
F(x)=y,\quad R(y)=x,\quad R(F(x))=x,\quad F(R(y))=y
\]

House 핵심값만 같거나 문장 의미만 같아서는 PASS가 아니다. 파일 순서, D/House 순서, 섹션·행·블록 배열, 표기, 대소문자, 상태문, 공백, 구분선, 개행까지 같아야 한다.

## 명시적 판단 프로토콜

다음 프로토콜은 차트 ID를 보지 않고 각 좌표에 동일하게 적용한다.

1. **파일 인벤토리**
   - 활성 D마다 SC7 Rashi 1, SC7 Bhava 1, SC8 Rashi 1, SC8 Bhava 1을 요구한다.
   - 각 문서에 1H~12H가 정확히 한 번씩 있어야 한다.
   - 누락은 EMPTY가 아니라 `HOLD-MISSING-COORDINATE`다.

2. **lane 독립 파싱**
   - Rashi는 `Visible Rashi Chart Snapshot`을 원본 좌표로 삼는다.
   - Bhava는 `Visible House Distribution`과 `Visible Bhava Structure`를 원본 좌표로 삼는다.
   - Rashi actor set과 Bhava actor set은 별도 필드로 유지한다.

3. **토큰 상태화**
   - 명시적 `EMPTY`, `NOT_SHOWN`, `HOLD`, `VOID`, `N.A.`, `SUPPORT_ONLY`를 서로 다른 enum으로 저장한다.
   - `NOT_SHOWN`은 절대 `EMPTY`로 바꾸지 않는다.
   - support actor는 primary actor로 승격하지 않는다.

4. **객체 레코드화**
   - actor, degree, sign, nakshatra, pada, RL/NL/SL/SSL을 하나의 레코드로 묶는다.
   - source record order도 별도 보존한다.
   - actor가 같아도 degree/circuit source가 다르면 합치지 않는다.

5. **기계 파생**
   - 모든 degree가 보일 때만 오름차순 order를 만든다.
   - 동률은 source order를 유지한다.
   - gap은 인접 degree의 60진수 차로 계산한다. gap으로 원 degree를 역추정하지 않는다.
   - 누락 회로는 계산하지 않는다.

6. **Rashi 직렬화**
   - full source board → planet joint board → co-presence board → 1H~12H slot → footer 순서를 따른다.
   - House function/linked houses는 house 번호에 대한 문법 상수다.
   - EMPTY/SINGLE/CO-PRESENCE 블록은 actor cardinality 조건으로 선택한다.

7. **Bhava 직렬화**
   - Bhava full distribution은 Bhava source에서만 만든다.
   - Rashi source link는 별도 참조 블록에만 둔다.
   - Bhava actor의 degree/circuit 보강은 같은 SC7 Bhava planetary row가 명시적으로 존재할 때만 허용한다.

8. **Rashi–Bhava 결속**
   - 같은 D×House의 두 primary set과 support set을 비교한다.
   - SAME/MAINTAINED/PARTIAL/MOVED/RE-FUNCTIONED는 명시적 위치·집합 근거가 있을 때만 선택한다.
   - 상태문은 검산용 derived 값이며 어느 lane도 덮어쓰지 않는다.

9. **역직렬화**
   - Rashi full source link와 Bhava full distribution을 각각 독립 복원한다.
   - 반복된 Seed 문장은 원자 복원의 단독 source가 아니라 checksum으로 사용한다.
   - 반복 occurrence가 다르면 임의 선택하지 않고 HOLD한다.

10. **최종 gate**
    - 생성 bytes의 SHA-256과 대응 정본 bytes를 비교한다.
    - 불일치는 수동 수정하지 않고 원자→조건→프로필 선택 단계로 되돌린다.

## Rashi 문법

### 입력 필드

직접 source:

- D, dataset title, subject/source/status 메타
- 1H~12H sign
- house별 occupant record 또는 EMPTY/NOT_SHOWN
- visible planetary positions
- visible RL/NL/SL/SSL
- visible support marker

파생 가능 field:

- actor cardinality state
- degree order와 인접 gap
- Nakshatra/Pada flow
- circuit flow
- 중복 source link
- fixed 30-frame seed의 source 자리

파생 불가 field:

- SC7에 없는 degree/nakshatra/circuit
- source가 말하지 않은 lordship·해석값
- 역사적 template version selector

### 명칭 변환

19개 non-D1 Rashi 대응쌍에서 다음 표기 변환이 반복 검출됐다.

| SC7 token | SC8 token |
|---|---|
| `P.Phalguni` | `Purva Phalguni` |
| `U.Phalguni` | `Uttara Phalguni` |
| `P.Ashadha` | `Purva Ashadha` |
| `U.Ashadha` | `Uttara Ashadha` |
| `P.Bhadrapada` | `Purva Bhadrapada` |
| `U.Bhadrapada` | `Uttara Bhadrapada` |
| `Aridra` | `Ardra` |
| `Jyeshta` | `Jyeshtha` |
| `Dhanishta` | `Dhanishtha` |

이 표는 관측된 문자열 transduction이며 조티시 값을 계산한 것이 아니다. 역변환은 역사적 non-D1 Rashi 프로필이 명시된 경우에만 적용한다. D1이나 미래 프로필에서 full spelling을 임의 축약하지 않는다.

### 상태 선택

| 조건 | Rashi state | 블록 |
|---|---|---|
| 확인된 primary actor 0 | `EMPTY` | lord-only/empty 고정문 |
| primary actor 1 | `SINGLE` | single 고정문 |
| primary actor ≥2 | `CO-PRESENCE` | order/gap 고정문 |
| occupant visibility 불명 | `HOLD/NOT_SHOWN` | 생성 중단 또는 typed HOLD |

관측 분포는 EMPTY 93, SINGLE 74, CO2 48, CO3 16, CO4 6, CO5 2, CO8 1로 총 240이다.

### 행·블록 순서

non-D1 Rashi 19문서는 공통 `RASHI_TARGET_FULL30` 계열이다.

1. title/one-file lock
2. purpose와 source/target setting
3. missing rule와 quality/domain lock
4. full house source board
5. planet joint board
6. co-presence order board
7. 2-1H부터 2-12H slot
8. slot 내부 auto-map → source extraction → linked structure → state rule → extraction board → Seed 30 → use decision
9. 공통 footer와 terminal metadata

D1은 별도의 역사적 profile이다. 첨부된 새 D1 empty template은 `D1FAMILY / EMPTY_TYPED_SLOTS` 계열이라 역사적 `OPTIMAL_2SPLIT / ACTUAL FILLED` Applied skeleton과 동일하지 않다.

## Bhava 문법

Bhava는 Rashi 문법의 복사본이 아니다.

### 입력 필드

- `Visible House Distribution`: Bhava primary/support actor
- `Visible Planetary Positions for Bhava Chart`: Bhava actor의 명시적 degree/sign/nak/pada/circuit
- `Visible Bhava Structure`: Begin/Middle 또는 Start/Cusp source
- 같은 D×House의 Rashi source link: 독립 참조용

### Bhava 고유 상태

| source 관계 | 상태 |
|---|---|
| Bhava primary 0, support 0 | `EMPTY / NONE / LORD_ONLY_OPERATION` |
| Bhava primary 0, support >0 | `SUPPORT_ONLY` |
| primary 1 | `SINGLE` |
| 동일 house의 다중 core 유지 | `MAINTAINED` |
| Rashi core의 엄격한 일부만 유지 | `PARTIAL_MAINTAINED` |
| 명시적으로 다른 house로 이동 | `MOVED` |
| source가 현실 기능 재배치를 명시 | `RE-FUNCTIONED` |
| 관계 source 부족 | `HOLD` |

관측된 SC7 Bhava 분포는 EMPTY 105, EMPTY+SUPPORT 7, SINGLE 70, SINGLE+SUPPORT 8, CO2 33, CO2+SUPPORT 2, CO3 9, CO3+SUPPORT 2, CO4 3, CO4+SUPPORT 1로 총 240이다.

### D1 alias

D1 역사적 Applied 문서에서만 다음 display alias가 관측됐다.

- `Lagna → As`
- `Rahu → Rahu(R)`
- `Ketu → Ketu(R)`
- `Maandi/Md SUPPORT_ONLY → Maandi visible as Md / SUPPORT_ONLY`

IR에서는 원 actor identity와 display token을 분리한다. alias를 actor identity 변화로 처리하지 않는다.

### 역사적 프로필 갈림

non-D1 Bhava 19문서에는 두 skeleton이 있다.

| 프로필 | 문서 수 | 구조 특징 |
|---|---:|---|
| `BHAVA_TARGET_LONG` | 13 | house slot마다 Additional Required Houses/Reason와 긴 footer 포함 |
| `BHAVA_TARGET_SHORT` | 6 | 위 행과 일부 rule footer 생략 |

두 계열 모두 핵심 source/state 구조는 같지만 SC7에 `TEMPLATE_VERSION`이나 같은 의미의 선택 원자가 없다. D 번호 목록을 selector로 쓰면 차트 ID 기반 예외표가 되므로 금지했다. 이 selector가 공급되기 전에는 전체 Bhava bytes 정방향 생성이 하나로 결정되지 않는다.

## Rashi·Bhava 결속문법

결속은 두 lane의 overwrite가 아니라 typed join이다.

| 출력 block | Rashi source | Bhava source | 생성 방식 |
|---|---|---|---|
| Rashi full board | 필수 | 사용 안 함 | Rashi 독립 |
| Bhava full distribution | 사용 안 함 | 필수 | Bhava 독립 |
| Rashi source link in Bhava | 필수 | 위치만 | 참조 복사 |
| Same/Moved/Partial/Re-functioned | 필수 | 필수 | 두 primary/support set 비교 |
| Bhava degree order/gap | 참조 checksum | 필수 | Bhava 위치의 명시 actor만 |
| Bhava Seed 1-2, 12, 17~20, 29 | 필수 | 필수 | 두 lane typed join |
| Rashi Seed 30 | 필수 | 사용 안 함 | Rashi 독립 |

`Rashi actor in H`와 `Bhava actor in H`를 같은 필드에 저장하지 않는다. 결속 후에도 `source_lane` tag를 유지하며 역변환은 tag별로 원 lane에 돌려놓는다.

## 왜 현재 exact inverse가 수학적으로 성립하지 않는가

### 1. 정의역 부족

요청 집합의 크기는 600인데 제공 집합은 480이다. 제공되지 않은 120개에 대해서는 규칙 검증도 반례 검사도 할 수 없다. 이를 600으로 세면 source 없는 값을 추정한 것이 된다.

### 2. 역사적 SC8의 비단사성

SC7에는 Source App Note, Header Data의 일부 행, Visible Note Text, Prior Control Notes, 세부 Lock Status, 빈 줄 run이 있다. 역사적 SC8은 이 모든 token을 고유하게 운반하지 않는다.

SC7 문서 `x1`과 `x2`가 house/planet source는 같고 SC8에 실리지 않는 Note 한 줄만 다르다고 하자. 현재 관측된 forward grammar에서는 `F(x1) = F(x2)`다. 그러면 하나의 `y`에 대해 `R(y)`가 `x1`과 `x2`를 동시에 복원할 수 없으므로 exact inverse가 존재하지 않는다. 해결하려면 SC8에 lossless carrier를 추가하거나, 복원 대상 SC7을 명시적으로 canonical subset으로 재정의해야 한다. 어느 쪽도 현재 source 계약에 없다.

### 3. forward profile selector 부재

동일한 SC7 atom schema에서 Bhava long/short 역사적 skeleton 두 개가 관측되지만, selector가 입력에 없다. D별 목록을 외부 lookup으로 두는 방법은 차트 ID 하드코딩이므로 채택하지 않았다.

### 4. D1 template version 불일치

첨부한 새 empty template의 고정문·block 깊이·placeholder 문장은 역사적 D1 Applied와 다르다. 새 템플릿을 채우면 새 canonical D1은 만들 수 있어도 제공된 역사적 SC8 bytes와 같아지지 않는다.

## 검증 결과

| Gate | 결과 | 판정 |
|---|---:|---|
| D folder 발견 | 20/20 | PASS |
| SC7 Rashi house | 240/240 | PASS |
| SC8 Rashi house | 240/240 | PASS |
| SC7 Bhava house | 240/240 | PASS |
| SC8 Bhava house | 240/240 | PASS |
| sign + actor multiset 핵심 결속 | 480/480 | PASS |
| 요청 source 수 | 480/600 | HOLD |
| Rashi 전체 TXT 정방향 exact | 0/240, 240 HOLD | HOLD |
| Rashi 전체 TXT 역방향 exact | 0/240, 240 HOLD | HOLD |
| Bhava 전체 TXT 정방향 exact | 0/240, 240 HOLD | HOLD |
| Bhava 전체 TXT 역방향 exact | 0/240, 240 HOLD | HOLD |
| 전체 byte roundtrip | 0/480, 480 HOLD | HOLD |
| 수동 보정 | 0 | PASS |
| chart-ID 예외 | 0 | PASS |

`0 exact`은 480개가 값 불일치했다는 뜻이 아니다. 완전 renderer/inverse의 선행조건이 성립하지 않아 **모두 실행 보류**했으며, 어떤 문서도 거짓 PASS나 수동 보정으로 통과시키지 않았다는 뜻이다.

## 실행

두 실행기는 ALL ZIP을 직접 읽거나 펼친 D 디렉터리를 읽는다.

```bash
./forward_sc7_to_sc8 \
  --sc7-root ../SC7/HYEWON_SC7_RASHI_BHAVA_20D_ALL.zip \
  --sc8-reference-root ../SC8/HYEWON_SC8_RASHI_BHAVA_20D_ALL.zip \
  --output forward_result.json
```

```bash
./reverse_sc8_to_sc7 \
  --sc7-root ../SC7/HYEWON_SC7_RASHI_BHAVA_20D_ALL.zip \
  --sc8-reference-root ../SC8/HYEWON_SC8_RASHI_BHAVA_20D_ALL.zip \
  --output reverse_result.json
```

현재 두 명령은 JSON core IR/coverage를 만들고 종료코드 2를 반환한다. `no_output_txt_emitted: true`가 안전장치다. 완전 문법이 증명되기 전에 target처럼 보이는 가짜 TXT를 만들지 않는다.

## HOLD 해제에 필요한 최소 입력

1. 요청한 600의 단위를 명시한 manifest와 현재 ZIP에 없는 120개 SC7↔SC8 대응쌍.
2. Bhava long/short를 SC7 원자에서 선택하는 명시적 non-ID field, 또는 하나의 canonical profile로 재정의한다는 계약.
3. SC8에 실리지 않는 SC7 메타·노트·공백을 위한 reversible carrier 규격, 또는 역복원 대상을 core canonical SC7으로 줄이는 계약.
4. D1의 target을 역사적 Applied로 유지할지, 첨부한 신형 typed template로 버전 상승할지에 대한 profile lock.

이 네 항목이 공급되면 같은 규칙표에 조건을 추가하고 exact renderer를 활성화한 뒤 600개 전체 SHA-256 gate를 다시 수행한다. 개별 차트 예외표나 수동 수정은 추가하지 않는다.
