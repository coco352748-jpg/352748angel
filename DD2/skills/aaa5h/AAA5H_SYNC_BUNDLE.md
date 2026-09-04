# AAA5H DD2 5H 20D LOCK SKILL PACK FNa98
SYNC_TARGET=$aaa5h
SYNC_MODE=GitHub remote sync bundle
SOURCE_WINDOW=PRIMARY
COMMANDS=$oo2 + $rq-sc3 + $rq-nak
OUTPUT_DEFAULT=문단형 점검문 / no 《 》 / D5 5H sentence-slot style
---


## FILE: README.md
```text
$aaa5h=ACTIVE_ALIAS / TARGET=5H×20D_LOCK_SKILL_PACK / COMMANDS=$oo2+$rq-sc3+$rq-nak

# DD2 5H 20D LOCK SKILL PACK

이 ZIP은 5H × 20D Rashi 잠금문 생산을 위한 복원/실행 스킬팩이다.

사용 방식:
1. 새 탭에서 SOURCE_WINDOW 파일을 올린다.
2. RESTORE_CALL.txt의 호출문을 붙인다.
3. `$rq-5h20d-one D6` 또는 `$rq-5h20d`로 실행한다.
4. 출력은 D5 5H 점검문 결을 유지하되 각 D차트 실제값과 도메인으로 치환한다.

핵심 적용:
- $oo2 = 왕복검증
- $rq-sc3 = D#×5H×Sign 좌표/도메인 고정
- $rq-nak = Nakshatra·Pada·RL/NL/SL/SSL 회로 적용

주의:
- 이 팩은 서버 내장 스킬이 아니라 파일 기반 복원/생산 지침팩이다.
- 소스 없는 값은 생성하지 않고 HOLD 처리한다.
```


## FILE: AAA5H_ALIAS_LOCK.md
```text
# $aaa5h ALIAS LOCK

ALIAS_KEY=$aaa5h
TARGET_PACK=DD2_5H_20D_LOCK_SKILL_PACK_FNa98
FUNCTION=5H×20D 잠금문 생산 스킬팩
ACTIVE_COMMANDS=$oo2 + $rq-sc3 + $rq-nak
SOURCE_WINDOW=PRIMARY
DRIVE=BACKUP_ONLY_IF_EXPLICITLY_REQUESTED
GITHUB=NOT_APPLIED

## ACTIVE MEANING
$aaa5h 호출 시 다음을 복원한다.
1. 20D 전체의 5H Rashi 잠금문 생산 경로.
2. D5 5H 점검문 문장결 앵커.
3. 꺾쇠표시 없는 문단형 점검문 형식.
4. $oo2 왕복검증.
5. $rq-sc3 좌표·도메인 고정.
6. $rq-nak Nakshatra·Pada·RL/NL/SL/SSL 회로 적용.

## HARD LOCK
- $aaa5h는 D5 5H 문장결을 20D 5H 생산 스킬로 호출하는 alias다.
- $aaa5h는 차트값을 생성하지 않는다. 소스창 PRIMARY의 실제값만 호출한다.
- $aaa5h는 문장수·문장결·점검문 흐름을 임의 변경하지 않는다.
- $aaa5h는 《 》 기호를 기본 출력에서 사용하지 않는다.
- $aaa5h는 번호형 체크리스트가 아니라 문단형 점검문을 출력한다.

## OUTPUT DEFAULT
TITLE=HYEWON_D##_5H_RASHI_DeF_BoArD_♤
STATUS=2.5차_98REV_LOCK_READY / $aaa5h_ACTIVE / RASHI_ONLY / BHAVA_PENDING
```


## FILE: SKILL.md
```text
$aaa5h=ACTIVE_ALIAS / TARGET=5H×20D_LOCK_SKILL_PACK / COMMANDS=$oo2+$rq-sc3+$rq-nak

# DD2 5H 20D LOCK PRODUCTION SKILL PACK FNa98

## PURPOSE
이 팩은 DD2 Chart 프로젝트에서 20D Rashi 5H 잠금문을 생산하기 위한 실행 스킬이다.
출력 목표는 D5 5H 점검문 결을 기준으로, 각 D차트의 5H 실제값과 도메인을 치환해 2.5~3단계 품질의 잠금문을 만드는 것이다.

서버 내장 또는 시스템 등록 완료를 주장하지 않는다. 이 팩은 소스창 PRIMARY를 읽어 실행하는 프로젝트 지침 기반 복원/생산 팩이다.

## CALL KEYS
- `$rq-5h20d` = 20D 전체 5H 잠금문 생산.
- `$rq-5h20d-one D#` = 특정 D차트 5H 잠금문 생산.
- `$rq-5h20d-check D#` = 특정 D차트 5H 소스/문장결/게이트 점검.
- `$oo2` = 범위잠금 → SC3 좌표 → 실제 차트 Source → 문장·슬롯 조립 → OO2 왕복검증.
- `$rq-sc3` = D_CHART × HOUSE × SIGN 좌표 및 도메인 레퍼런스 제공. 실제 차트값을 대체하지 않는다.
- `$rq-nak` = Nakshatra·Pada 및 RL/NL/SL/SSL 회로 레퍼런스 제공. 목표 소스가 있을 때만 적용한다.

## 20D ORDER
D1 → D9 → D2 → D3 → D4 → D5 → D6 → D7 → D8 → D10 → D11 → D12 → D16 → D20 → D24 → D27 → D30 → D40 → D45 → D60

D50은 현재 작업 대상에서 제외한다.

## SOURCE AUTHORITY
1. 현재 소스창 파일 = PRIMARY.
2. 현재 대화에서 사용자가 직접 제공한 잠금문/교정 = LOCAL ACTIVE, 지정 범위만 적용.
3. Google Drive = BACKUP only, 사용자가 연결 요청한 경우에만 조회.
4. Git/GitHub 원격 = 이 팩의 기본 실행에서 제외.
5. 사용자 승인 정본 외 자료는 VOID 재활성화 금지.

## REQUIRED INPUT PER D-CHART
각 D차트 5H 생산 전 아래 값이 실제 소스에서 확인되어야 한다.

- D Chart name
- Rashi Lagna
- 5H sign
- 5H occupants
- 5H lord
- 5H lord position: degree, sign, nakshatra, pada, house
- 5H lord RL/NL/SL/SSL
- co-presence in the 5L house
- 11H opposite/recovery axis
- D-chart domain
- linked houses used in output

값이 없으면 생성하지 않고 HOLD 처리한다. 일반지식으로 채우지 않는다.

## OUTPUT STYLE LOCK
- 점검문은 번호형 체크리스트가 아니다.
- D5 5H처럼 문단형 잠금문으로 출력한다.
- `《 》` 기호는 사용하지 않는다.
- 문장 안에서 정의 → 검문 → 조건 → 이동 → 누수 → 회수 → 절단 → 최종 잠금이 흘러야 한다.
- 넓은 표는 최종 잠금문 출력 본문에 넣지 않는다.
- 소스값은 SOURCE DATA에만 명시한다.
- 본문은 Rashi-only 기준으로 유지한다. Bhava는 사용자가 요청할 때만 별도 적용한다.
- Aspect/Bala/Ashtakavarga/Mrityu/SP/AVA/Dasha/Transit는 소스와 요청이 있을 때만 적용한다.

## `$oo2` APPLICATION
OO2는 생성기가 아니라 왕복검증 게이트다.

1. TARGET LOCK: D# Rashi 5H로 고정한다.
2. SOURCE LOCK: 소스창 D# Rashi source와 도메인만 사용한다.
3. SC3 COORDINATE: D# × 5H × sign 좌표를 고정한다.
4. NAK CIRCUIT: 5L 및 관련 행성의 Nakshatra·Pada·RL/NL/SL/SSL을 호출한다.
5. SENTENCE SLOT: D5 5H 점검문 결을 유지해 치환한다.
6. ROUND TRIP: 출력문에서 다시 SOURCE DATA를 역추출해 원값과 비교한다.
7. FAIL 처리: 소스값이 바뀌었거나 문장결이 깨지면 REVISE, 소스가 없으면 HOLD.

## `$rq-sc3` APPLICATION
SC3는 좌표 레퍼런스다.

- D-chart 도메인과 해당 house/sign의 기능을 제공한다.
- 실제 행성 위치, 도수, 나크샤트라, 파다, RL/NL/SL/SSL 값은 반드시 원천 소스에서 가져온다.
- SC3가 실제값을 대체하면 HARD FAIL.

## `$rq-nak` APPLICATION
NAK는 나크샤트라·파다 및 회로 레퍼런스다.

적용 대상:
- 5H lord
- 5L house co-presence planet
- 5H occupant가 있는 경우 occupant set
- 11H/3H/7H/12H 등 본문 연결축에 실제 행성 설명이 들어가는 경우

금지:
- 원천 소스 없는 nak/pada 생성
- RL/NL/SL/SSL 보정
- 나크샤트라 의미를 도메인보다 우선시키기

## PRODUCTION SEQUENCE
각 D차트 5H 잠금문은 다음 순서로 출력한다.

1. Header
2. SOURCE BASIS
3. SOURCE DATA
4. D# Rashi 5H 기본 정의
5. 5H sign door
6. 5H lord section
7. 5L house operation field: 공동장 또는 단독장
8. 5H → 5L house movement joint
9. 9H law/execution connection
10. 5L house direct connection
11. 3H 기준문 connection
12. 7H 검증 connection
13. 11H 회수 connection
14. 12H 소모 connection
15. 2H / 4H resource-foundation connection
16. 막힘 위치
17. 과출력 / 과소작동 조건
18. 절단 조건
19. 현실 규칙
20. 최종 잠금문
21. 한 줄 잠금
22. TITLE / INDEX / STATUS

## FNa98 GATE
PASS 조건:
- TARGET이 D# Rashi 5H에서 벗어나지 않는다.
- SOURCE DATA와 본문 실제값이 일치한다.
- 도메인은 D# source/domain에서만 온다.
- D5 5H 점검문 결이 유지된다.
- 문장 추가/삭제/합치기로 문장결을 깨지 않는다.
- `《 》` 없이 점검문 형식으로 출력한다.
- `$oo2`, `$rq-sc3`, `$rq-nak` 적용 위치가 분리되어 있다.

REVISE 조건:
- 문장결은 맞지만 소스값 누락, 순서 오염, 연결축 과다/부족이 있다.

HOLD 조건:
- 5H lord 값, 도메인, nak/pada, RL/NL/SL/SSL 중 필수값이 확인되지 않는다.

## FILES IN THIS PACK
- `SKILL.md` = 이 파일.
- `20D_5H_SOURCE_INDEX.tsv/json` = 소스창에서 파싱한 20D Rashi 5H 기본 인덱스.
- `SOURCE_WINDOW_MANIFEST.tsv/json` = 현재 소스창 파일명·크기·SHA256.
- `OUTPUT_TEMPLATE_CHECK_STYLE.md` = 점검문 출력 템플릿.
- `D5_5H_STYLE_ANCHOR.md` = D5 5H 점검문 결 앵커.
- `COMMAND_ROUTER.md` = $oo2/$rq-sc3/$rq-nak 라우팅 규칙.
- `QA_GATE.md` = 출력 전후 검산 게이트.
- `RESTORE_CALL.txt` = 새 탭 복원 호출문.
```


## FILE: COMMAND_ROUTER.md
```text
$aaa5h=ACTIVE_ALIAS / TARGET=5H×20D_LOCK_SKILL_PACK / COMMANDS=$oo2+$rq-sc3+$rq-nak

# COMMAND ROUTER

TARGET: 5H × 20D Rashi 잠금문 생산
ACTIVE COMMANDS: $oo2 + $rq-sc3 + $rq-nak

## ROUTE
1. $rq-5h20d 호출 시 20D order 전체를 순회한다.
2. 각 D마다 $rq-sc3로 D# × 5H × Sign 좌표와 도메인만 고정한다.
3. 실제값은 HYEWON_VeDic_D1-D60_♤-1.txt의 Rashi source에서 가져온다.
4. $rq-nak은 5L/occupant/co-presence의 Nakshatra·Pada·RL/NL/SL/SSL 회로에만 적용한다.
5. $oo2는 출력 후 역추출 검증으로 적용한다.

## HARD LIMITS
- SC3는 실제 차트값 대체 금지.
- NAK는 소스 없는 파다/회로 생성 금지.
- OO2는 문장수와 값 일치 검산용이지 임의 확장용이 아니다.
- Bhava, Aspect, Bala, Ashtakavarga, Dasha, Transit는 기본 미적용.
- 출력은 점검문 문단형. 번호형 체크리스트 금지.
```


## FILE: OUTPUT_TEMPLATE_CHECK_STYLE.md
```text
# OUTPUT TEMPLATE CHECK STYLE

D# Rashi 5H [SIGN]

━━━━━━━━━━━━━━━━━━━━━━━━
HYEWON_D#_5H_RASHI_DeF_BoArD_♤
D# Rashi 5H [SIGN] / 5H [OCCUPANT_STATUS] / 5L [LORD] in [LORD_SIGN] [LORD_HOUSE] [WITH_OR_SINGLE]
2.5차 98 정본 잠금문
D5 5H SENTENCE_SLOT_STYLE / [D# DOMAIN] DENSE LOCK 품질 적용
[KEYWORD_01] / [KEYWORD_02] / [KEYWORD_03] / [KEYWORD_04] / [KEYWORD_05]
━━━━━━━━━━━━━━━━━━━━━━━━

SOURCE BASIS
- Subject Code = HYEWON
- Chart = [D# FULL NAME] Rashi
- Source Layer = HYEWON [D# FULL NAME] Rashi / Blue app Rashi structure
- Rashi Layer = controlling layer
- Bhava Layer = not applied in this file
- Hidden / non-visible values = not assumed
- Aspect / Bala / Ashtakavarga / Mrityu / SP / AVA / Dasha / Transit = not applied in this file

SOURCE DATA
- Lagna = [LAGNA]
- Target House = 5H from [LAGNA] Lagna
- 5H Sign = [5H_SIGN]
- 5H Occupants = [5H_OCCUPANTS]
- 5H Lord = [5L]
- 5H Lord Position = [5L] [DEGREE] [SIGN] / [NAKSHATRA] P[PADA] / House [HOUSE] / RL [RL] / NL [NL] / SL [SL] / SSL [SSL]
- [5L_HOUSE] Operation Field = [CO_PRESENCE_OR_SINGLE]
- Opposite House = 11H [11H_SIGN] [11H_STATUS] / 11L [11L_ROUTE]
- Linked Houses = 5H / [5L_HOUSE] / 11H / 12H / 3H / 7H / 2H / 4H / 9H / 10H
- D# Domain = [DOMAIN]

본문은 D5 5H 점검문 결을 따른다.
번호형 점검 01 금지.
꺾쇠표시 금지.
문단형 잠금문 유지.
```


## FILE: D5_5H_STYLE_ANCHOR.md
```text
# D5 5H STYLE ANCHOR

이 앵커는 5H × 20D 생산의 문장결 기준이다.

## 형식 기준
- 점검문은 번호형 체크리스트가 아니다.
- 꺾쇠표시를 쓰지 않는다.
- 문단형 잠금문으로 출력한다.
- SOURCE BASIS와 SOURCE DATA를 먼저 둔다.
- 본문은 하우스 정의 → sign door → empty/lord → lord section → 작동장 → 이동관절 → 연결축 → 막힘 → 과출력 → 절단 → 현실규칙 → 최종잠금 순서로 간다.

## D5 5H 핵심 결
D5 5H Cancer는 권위와 공덕이 무엇에 마음을 주고 무엇을 품어 키울 것인가로 열리는 자리다.
하지만 일반 5H 의미가 아니라, D5 도메인 안에서 권위 자원과 공덕 자원을 어디에 투입해도 되는지 심사하는 자리다.

5H가 empty이면 하우스 내부에서 직접 폭발하지 않고 5H lord 이동처를 따라간다.
5L Moon이 Sagittarius 10H로 가므로 보호감 자원은 공적 출력, 명분 행동, 체감, 명예로 올라가야 한다.

좋은 점검문은 문장 안에서 계속 묻는다.
- 이 자원은 도메인에 맞는가.
- 이 자원은 기준문으로 내려오는가.
- 이 자원은 관계검증을 통과하는가.
- 이 자원은 회수되는가.
- 이 자원은 12H 소모로 빠지는가.
- 이 자원은 2H/4H를 털어먹는가.
- 이 자원은 절단 후에도 남는가.

## 치환 원칙
D5 5H의 자원투입 문법은 각 D차트 도메인으로 바꾼다.
예: D6에서는 권위 자원 → 문제 판단, 공덕 자원 → 손실방어 판단, 보호감 → 즉시 반응, 회수 → 회복 회수.
```


## FILE: QA_GATE.md
```text
# QA GATE FNa98

## PRE-GENERATION CHECK
- TARGET = D# Rashi 5H인가.
- SOURCE = HYEWON_VeDic_D1-D60 Rashi source인가.
- DOMAIN = D# usage/domain인가.
- Rashi-only인가.
- Bhava/Aspect/Bala/Transit 등 미요청 레이어를 섞지 않았는가.
- 5H sign/lord/occupant/5L position/RL/NL/SL/SSL 확인 완료인가.

## POST-GENERATION CHECK
- Header의 SOURCE DATA와 본문 실제값이 일치하는가.
- D5 5H 점검문 결을 유지하는가.
- 번호형 체크리스트가 아닌 문단형인가.
- 꺾쇠표시가 없는가.
- 일반 하우스 의미로 빠지지 않았는가.
- D-chart 도메인이 본문 전체에 유지되는가.
- 결론이 막힘/절단/회수/현실규칙/최종잠금까지 닫히는가.

## VERDICT
PASS = 그대로 납품 가능.
REVISE = 소스는 있으나 문장결/순서/누락 수정 필요.
HOLD = 필수 소스값 부족 또는 권위 충돌.
```


## FILE: RESTORE_CALL.txt
```text
$aaa5h=ACTIVE_ALIAS / TARGET=5H×20D_LOCK_SKILL_PACK / COMMANDS=$oo2+$rq-sc3+$rq-nak

$rq-5h20d
SOURCE_WINDOW=PRIMARY
TARGET=HYEWON 20D Rashi 5H lock production
STYLE_ANCHOR=D5 5H check-style lock sentence
COMMANDS=$oo2 + $rq-sc3 + $rq-nak
ORDER=D1,D9,D2,D3,D4,D5,D6,D7,D8,D10,D11,D12,D16,D20,D24,D27,D30,D40,D45,D60
OUTPUT=문단형 점검문 / 꺾쇠표시 없음 / Rashi-only / 2.5~3단계 / FNa98 gate
FORBID=VOID reuse, source fabrication, Bhava mixing, numbered checklist, unrequested Aspect/Bala/Dasha/Transit
```


## FILE: 20D_5H_SOURCE_INDEX.tsv
```text
D	Subtype	DomainUsage	Lagna	Lagna_skt	5H_sign	5H_sign_skt	5H_occupants	5L	5L_degree	5L_sign	5L_sign_skt	5L_house	5L_nakshatra	5L_pada	5L_RL	5L_NL	5L_SL	5L_SSL	11H_sign	11H_sign_skt	SourceStatus
D1	D1 Rashi / Baseline Reference Dataset	baseline document for Vedic house-analysis tabs and derivative chart comparison	Virgo	Kanya	Capricorn	Makara	Ketu	Saturn	4:52:46	Virgo	Kanya	1H	U.Phalguni	3	Me	Su	Sa	Ju	Cancer	Kataka	PARSED_FROM_HYEWON_VeDic_D1-D60_RASHI
D9	D9 Navamsha / Rashi-style Reference Dataset	dharma / marriage / deep-strength comparison layer	Taurus	Vrishabha	Virgo	Kanya	Moon+Venus+Pluto	Mercury	15:07:09	Aquarius	Kumbha	10H	Shatabhisha	3	Sa	Ra	Me	Ra	Pisces	Meena	PARSED_FROM_HYEWON_VeDic_D1-D60_RASHI
D2	D2 Hora / Rashi-style Wealth Resource Dataset	direct resource / wealth tone / value handling reference	Cancer	Kataka	Scorpio	Vrischika	Rahu+Ketu+Mars	Mars	13:27:44	Scorpio	Vrischika	5H	Anuradha	4	Ma	Sa	Ra	Ma	Taurus	Vrishabha	PARSED_FROM_HYEWON_VeDic_D1-D60_RASHI
D3	D3 Drekkana / Rashi-style Sibling Courage Dataset	sibling/courage/execution support layer	Pisces	Meena	Cancer	Kataka	Moon+Neptune+Pluto	Moon	5:00:49	Cancer	Kataka	5H	Pushyami	1	Mo	Sa	Me	Sa	Capricorn	Makara	PARSED_FROM_HYEWON_VeDic_D1-D60_RASHI
D4	D4 Chaturthamsha / Rashi-style Property-Residence Dataset	property / residence / inner base / asset foundation layer	Virgo	Kanya	Capricorn	Makara	Moon+Mars	Saturn	18:49:24	Virgo	Kanya	1H	Hasta	3	Me	Mo	Me	Sa	Cancer	Kataka	PARSED_FROM_HYEWON_VeDic_D1-D60_RASHI
D5	D5 Panchamsha / Rashi-style Authority-Merit Dataset	authority / merit / projected status / dignity expression layer	Pisces	Meena	Cancer	Kataka	empty	Moon	28:21:19	Sagittarius	Dhanus	10H	U.Ashadha	1	Ju	Su	Mo	Ve	Capricorn	Makara	PARSED_FROM_HYEWON_VeDic_D1-D60_RASHI
D6	D6 Shashtamsha / Rashi-style Struggle-Health Dataset	illness pressure / burden / enemies / debt / friction / service / problem-management layer	Sagittarius	Dhanus	Aries	Mesha	empty	Mars	20:46:27	Gemini	Mithuna	7H	Punarvasu	1	Me	Ju	Ju	Ke	Libra	Thula	PARSED_FROM_HYEWON_VeDic_D1-D60_RASHI
D7	D7 Saptamsha / Rashi-style Lineage-Creative Continuity Dataset	children / continuity / generative lineage / relational future layer	Aquarius	Kumbha	Gemini	Mithuna	empty	Mercury	27:04:17	Capricorn	Makara	12H	Dhanishtha	2	Sa	Ma	Ve	Su	Sagittarius	Dhanus	PARSED_FROM_HYEWON_VeDic_D1-D60_RASHI
D8	D8 Ashtamsha / Rashi-style Vulnerability-Transformation Dataset	vulnerability / crisis / rupture / hidden survival layer	Scorpio	Vrischika	Pisces	Meena	empty	Jupiter	10:09:54	Gemini	Mithuna	8H	Ardra	2	Me	Ra	Ju	Sa	Virgo	Kanya	PARSED_FROM_HYEWON_VeDic_D1-D60_RASHI
D10	D10 Dashamsha / Rashi-style Career-Status Dataset	profession / action-status / public role / authority execution layer	Virgo	Kanya	Capricorn	Makara	Moon+Pluto	Saturn	18:47:41	Gemini	Mithuna	10H	Ardra	4	Me	Ra	Mo	Ve	Cancer	Kataka	PARSED_FROM_HYEWON_VeDic_D1-D60_RASHI
D11	D11 Rudramsha / Rashi-style Gains-Obstruction Dataset	social gain / network pressure / obstruction-release layer	Libra	Thula	Aquarius	Kumbha	Mercury+Saturn	Saturn	1:32:01	Virgo	Kanya	12H	U.Phalguni	2	Me	Su	Sa	Sa	Leo	Simha	PARSED_FROM_HYEWON_VeDic_D1-D60_RASHI
D12	D12 Dvadashamsha / Rashi-style Parents-Ancestral Dataset	parents / ancestry / inherited root layer	Scorpio	Vrischika	Pisces	Meena	Moon+Ketu+Pluto	Jupiter	17:28:29	Aquarius	Kumbha	4H	Shatabhisha	4	Sa	Ra	Sa	Su	Virgo	Kanya	PARSED_FROM_HYEWON_VeDic_D1-D60_RASHI
D16	D16 Shodashamsha / Rashi-style Comfort-Vehicle Dataset	comfort / vehicles / happiness-enclosure / protected enjoyment layer	Pisces	Meena	Cancer	Kataka	empty	Moon	8:43:58	Pisces	Meena	1H	U.Bhadrapada	2	Ju	Sa	Ve	Ra	Capricorn	Makara	PARSED_FROM_HYEWON_VeDic_D1-D60_RASHI
D20	D20 Vimshamsha / Rashi-style Spiritual Practice Dataset	spiritual practice / mantra / devotion / inner discipline layer	Sagittarius	Dhanus	Aries	Mesha	Jupiter+Saturn+Rahu+Ketu	Mars	20:46:27	Aquarius	Kumbha	3H	P.Bhadrapada	1	Sa	Ju	Ju	Ke	Libra	Thula	PARSED_FROM_HYEWON_VeDic_D1-D60_RASHI
D24	D24 Chaturvimshamsha / Rashi-style Learning-Education Dataset	learning / study / vidya / intellectual formation layer	Aries	Mesha	Leo	Simha	Sun+Jupiter+Rahu+Neptune+Pluto	Sun	18:00:59	Leo	Simha	5H	P.Phalguni	2	Su	Ve	Me	Ve	Aquarius	Kumbha	PARSED_FROM_HYEWON_VeDic_D1-D60_RASHI
D27	D27 Bhamsha / Rashi-style Strength-Weakness Dataset	inner strength / weakness / embodied resilience layer	Scorpio	Vrischika	Pisces	Meena	Mars+Ketu+Saturn+Neptune	Jupiter	8:45:02	Capricorn	Makara	3H	U.Ashadha	4	Sa	Su	Sa	Sa	Virgo	Kanya	PARSED_FROM_HYEWON_VeDic_D1-D60_RASHI
D30	D30 Trimshamsha / Rashi-style Misfortune-Fault Dataset	misfortune / fault-line / hidden harm / affliction pattern layer	Aries	Mesha	Leo	Simha	Sun+Mercury+Ketu+Uranus	Sun	18:00:59	Leo	Simha	5H	P.Phalguni	2	Su	Ve	Me	Ve	Aquarius	Kumbha	PARSED_FROM_HYEWON_VeDic_D1-D60_RASHI
D40	D40 Khavedamsha / Rashi-style Auspiciousness-Maternal Line Dataset	maternal-line auspiciousness / inherited grace / subtle support layer	Leo	Simha	Sagittarius	Dhanus	Mars	Jupiter	13:09:55	Pisces	Meena	8H	U.Bhadrapada	3	Ju	Sa	Sa	Ra	Gemini	Mithuna	PARSED_FROM_HYEWON_VeDic_D1-D60_RASHI
D45	D45 Akshavedamsha / Rashi-style Character-Fortune Dataset	character imprint / inherited merit / subtle dharma fortune layer	Pisces	Meena	Cancer	Kataka	Moon+Ketu+Pluto	Moon	3:43:09	Cancer	Kataka	5H	Pushyami	1	Mo	Sa	Ra	Mo	Capricorn	Makara	PARSED_FROM_HYEWON_VeDic_D1-D60_RASHI
D60	D60 Shashtiamsha / Rashi-style Karma-Root Dataset	deep karmic root / inherited karmic imprint / hidden causality layer	Sagittarius	Dhanus	Aries	Mesha	empty	Mars	21:22:32	Sagittarius	Dhanus	1H	P.Ashadha	3	Ju	Ve	Ve	Me	Libra	Thula	PARSED_FROM_HYEWON_VeDic_D1-D60_RASHI
```


## FILE: SOURCE_WINDOW_MANIFEST.tsv
```text
filename	bytes	sha256
01_AB_D10_PicAcHu_☆.zip	325673	82bfea0b158e143aff639731de4d003971214754fb3fb00d5b4e1120e7c74190
01_AB_D11_PicAcHu_☆.zip	327326	25f3276c400dac62c9cda1b7804d4290ca2cc8ebbbbe46c42a4e711ce62a68eb
01_AB_D12_PicAcHu_☆.zip	320890	d781fc20a560d29c26812892b3f8778fa84c63c0f3feb33dcdf4603c2f7056a1
01_AB_D16_PicAcHu_☆.zip	319933	1abd3fabb89d9ee8ade6bf33d94dfa4b7f78af92a3697362b254257046faa8a0
01_AB_D1_PicAcHu_☆.zip	312922	b48a4236f993c83f4154847170f5864cf54ab8b642a263c21adf6ce6faa98ed0
01_AB_D20_PicAcHu_☆.zip	320632	67dc156dabf75a55429b325d08d71a392bd95d4963070ae9daea9f70360111be
01_AB_D24_PicAcHu_☆.zip	324290	3e23d584e2a36247f0732c75118df978479a946eb8c9048c42d64a70c0b31f3b
01_AB_D27_PicAcHu_☆.zip	322375	f68ad1967026871c0f7e3c5ec0e8ca2a8cfe4061be95ca1c94d4cb0fb4646fad
01_AB_D2_PicAcHu_☆.zip	320395	3ee6d9581fc694f811670014f883a6c0c8a3cb559c7c35a1bca9d212e299be92
01_AB_D30_PicAcHu_☆-1.zip	315107	bcfd26781831028e2e4a7ba38e632aa2e293aaadd672d59347614244446cde0d
01_AB_D3_PicAcHu_☆.zip	325544	eb27eb9453df717dbd29187ed9c9ab2d9e3bc43634203b256b263753620cb076
01_AB_D40_PicAcHu_☆.zip	321970	14e317d794a57d1168f6dc77ddc08671b237a505fdec4b11141351ed4b087ca7
01_AB_D45_PicAcHu_☆.zip	323673	22ba1f8763868a8212fc3cd4d7bacc0001fbc5f5e3d4c5678347d25554502e29
01_AB_D4_PicAcHu_☆.zip	326545	289130ad388328428eb86316958960d1c4476d6a8a40aa724a3a524aef5489f1
01_AB_D5_PicAcHu_☆.zip	324212	a26c0a512b5fa459b64f60c00d5ab8232ed2619e67dc27cfe7792c0f9b4c6688
01_AB_D60_PicAcHu_☆.zip	321845	ddcb893135df03452321e7eba9e4db377141343733e8b890cc09ca1f4126f6b5
01_AB_D6_PicAcHu_☆.zip	323947	993bc3081d3f86e141e9db1139b837999795f2ad74ef510d5bb0c5d69c6d2d1d
01_AB_D7_PicAcHu_☆.zip	325894	c300a8c882de36d647c28bb089bbecfc084003909d5709b9f378a4d91e206968
01_AB_D8_PicAcHu_☆.zip	323808	fc88c9b09a20c33d09753cdaf0bc39160b10609664c94e16ebb2974712fa40d6
01_AB_D9_PicAcHu_☆.zip	324481	e60dbc871dfa21a65cec418b94ed778a1a6c85db7827eefbba09a920392cdb0f
02A_DChart_AppLieD_.zip	489007	c7433d6d549b68282c6cd4f798b495f46364d7e64911222d31368a1119d78507
07_5AB_BhaBaLa_Aspect02_AppLieD.zip	341316	4087d79e301d02c4a47caeaabcc9babd04773bff77697e6c53f9e7c8fa654145
07_6AB_VimsoPaka_AsPecT_20D_AppLieD.zip	161816	c8c21165aa80d146d14418253134c7ca8435bf73015d0f1c91fc7b4297ff43a3
33_4AB_DriShTi_AlL_BoArD_AppL_.zip	179876	95bffb36119d77f4f38fd14c2e86c3cd65a60e61ed3b46893e6ff179753249b5
BHINNA_PLANET_D1-D60_♤.txt	713647	69b7179a6a9e51cccd2899396a19c4a50ceda93a43a6906976e56ff7b20066c1
HYEWON_ARUDHAS_♤.txt	76918	23ffebc3e8d758b0a97ff4a7a1a7268f144ecb4cdf092b99eb7dca1d53158487
HYEWON_ASHTA_SAP_TKS_EKS_SPD_♤.txt	290061	3b06c6db540fff821af3daed169bfce3d21cccef435a2aca3d83b3b905fcdd89
HYEWON_AVA_SPother_Mrityu_♤.txt	233099	b38730f537cd45dd2ba779262a49722ebb0e6db58cabeb7ec445257b8d558f6b
HYEWON_D1_ASPECTS_3_♤.txt	13061	f8eab4141c67df059113d8955954c1e9a6eae400ef869985937e43dbd2ef0303
HYEWON_D1_DASHA_2017-45_♤.txt	13203	bf1c365eb973eee6d18fd6bf27060728e0c55b784541d5bafdd7ff7adc8be031
HYEWON_ShaDbala_BhaVala_VimSo_♤.txt	20096	634803f8918f0f8fa724926cf28473ffc572d59eb3fc732bb60ac9b46521d723
HYEWON_VeDic_CO2_99.txt	206242	3b3d7a96af7653d0dfa240c4ff191c36522b4aeb634c21c2da13564684e7fd2f
HYEWON_VeDic_D1-D60_♤-1.txt	183093	49cc770f12ed1b932ded4aeb0cd934a87838dce12d6f21ddd4a034f1273cb6c2
```


## FILE: ALIAS_MANIFEST.json
```json
{
  "alias_key": "$aaa5h",
  "created_at": "2026-08-30T08:28:00+09:00",
  "pack_name": "AAA5H_DD2_5H_20D_LOCK_SKILL_PACK_FNa98",
  "active_commands": [
    "$oo2",
    "$rq-sc3",
    "$rq-nak"
  ],
  "source_authority": "SOURCE_WINDOW_PRIMARY",
  "files": [
    {
      "path": "20D_5H_SOURCE_INDEX.json",
      "sha256": "5107e9a48536067130e7af2fcae14ce9d2a6706b43c43f6d0091de5f5443f623",
      "bytes": 13692
    },
    {
      "path": "20D_5H_SOURCE_INDEX.tsv",
      "sha256": "d40b7da97077eab417edb8dceec8d002c9a9b2b8accc3dcb4306eb3835a5dd2a",
      "bytes": 5444
    },
    {
      "path": "AAA5H_ALIAS_LOCK.md",
      "sha256": "eea934f679aaa4b6cd84d69ab359d6f1ec2dfecf59e5d73c7dad456fe8cb8528",
      "bytes": 1137
    },
    {
      "path": "COMMAND_ROUTER.md",
      "sha256": "feaa5dbed567dde0d56a606d2964fa341b00d28bafa89fcdd59d67c235bf86f7",
      "bytes": 903
    },
    {
      "path": "D5_5H_STYLE_ANCHOR.md",
      "sha256": "b6eeb1899b6e58bb2c5c55c3a8c72c9d85db62a1e490878450dbfb8e6ea527b1",
      "bytes": 1607
    },
    {
      "path": "OUTPUT_TEMPLATE_CHECK_STYLE.md",
      "sha256": "52db1b9c95979ab90658cbc0b3e65b364599627b3870d4bff2c9838e310bbd1a",
      "bytes": 1455
    },
    {
      "path": "QA_GATE.md",
      "sha256": "58b4ce3dcafcbde3c5d220fa9600481bb979dd11e757a1c327f30abea06acfa5",
      "bytes": 892
    },
    {
      "path": "README.md",
      "sha256": "4aca82c687f7515ae6f928236c4bb96cca752965fb6404d2a9d47398f332881d",
      "bytes": 784
    },
    {
      "path": "RESTORE_CALL.txt",
      "sha256": "0a39b243c7b555c83ab954d70a23da8111a571a4f3f4e8895f107e5d54288ff2",
      "bytes": 517
    },
    {
      "path": "SKILL.md",
      "sha256": "20c6cf815f59c4faeae9b347c57c98930f49374e85a4cc147b91710ab3053971",
      "bytes": 5914
    },
    {
      "path": "SOURCE_WINDOW_MANIFEST.json",
      "sha256": "a09959f6cf1b5aa5f2bbcc2d5f27933852e56925fd169a6900fc82c576de63b6",
      "bytes": 5211
    },
    {
      "path": "SOURCE_WINDOW_MANIFEST.tsv",
      "sha256": "422298748f27a5f14aeec7dc4b85c37fda340b0abbcf08b85cc0782cc41b089a",
      "bytes": 3317
    }
  ]
}
```
