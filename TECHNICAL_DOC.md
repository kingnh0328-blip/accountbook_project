# Personal AccountBook 기술문서

---

## 0. 표지

- **프로젝트명**: Personal AccountBook
- **한 줄 소개**: 서버 렌더링 기반 Django 개인 가계부 웹 애플리케이션
- **개발 기간**: 2026.01 ~ 2026.02
- **팀 구성**: 팀 프로젝트 (3인)
  - 팀원 A: 인증 및 계좌 관리 (accounts 앱)
  - 팀원 B: 거래 관리 및 필터링 (transactions 앱)
  - 팀원 C: 대시보드 및 영수증 관리 (dashboard 앱)
- **기술 스택**
  - Backend: Django 4.2
  - Database: PostgreSQL
  - Frontend: Django Template (Server Rendering), Bootstrap 5
  - Deploy: Fly.io, Docker, Gunicorn
  - CI: GitHub Actions

---

## 1. 프로젝트 요약 (비즈니스 관점)

### 1.1 프로젝트 배경

- 개인 재무 관리에 대한 수요 존재
- 기존 가계부 앱은 과도한 기능으로 복잡도 높음
- 핵심 기능만 제공하는 경량 가계부 서비스 필요

### 1.2 핵심 가치

- 계좌 기반 입출금 기록 및 잔액 자동 관리
- 필터/검색 기반 거래 내역 조회
- 월별 수입/지출 요약 대시보드 제공

### 1.3 MVP 범위 정의

- 서버 렌더링(MVT) 기반 단일 Django 애플리케이션
- JavaScript 최소 사용 (카테고리 AJAX만 적용)
- JWT 미적용, 세션 기반 인증

### 1.4 MVP 기능 목록

- 1.4.1 사용자 인증 (회원가입 / 로그인 / 로그아웃)
- 1.4.2 계좌 CRUD (생성 / 조회 / 수정 / 삭제)
- 1.4.3 거래 CRUD (입금 / 출금 기록 관리)
- 1.4.4 필터 / 검색 / 정렬 (기간, 계좌, 카테고리, 키워드)
- 1.4.5 영수증 파일 업로드 (이미지 / PDF)
- 1.4.6 대시보드 요약 (월별 수입/지출, 카테고리별 통계, 달력)

---

## 2. 사용자 시나리오 및 화면 흐름 (행동 중심)

### 2.1 사용자 역할 정의

```
- User: 개인 계좌 및 거래 데이터 관리
- Admin: 운영 및 데이터 관리 목적 (superuser)
```

### 2.2 대표 사용자 여정

```
회원가입 → 로그인 → 계좌 생성 → 거래 등록 → 영수증 첨부 → 대시보드 확인
```

### 2.3 화면 흐름 다이어그램

```
[비인증]
   │
   ▼
로그인 / 회원가입
   │
   ▼
[인증]
   │
   ├──→ 계좌 목록 ──→ 계좌 상세 ──→ 계좌 수정/삭제
   │
   ├──→ 거래 목록 ──→ 거래 상세 ──→ 거래 수정/삭제
   │         │                │
   │         ▼                ▼
   │    필터/검색/정렬     영수증 업로드/삭제
   │
   ├──→ 카테고리 관리 ──→ 카테고리 생성/삭제
   │
   └──→ 대시보드 ──→ 월별 통계 / 카테고리별 통계 / 달력
```

### 2.4 흐름 해설

- 비인증 사용자는 로그인 또는 회원가입 화면만 접근 가능
- 인증 완료 시 대시보드가 기본 진입점 역할 수행
- 계좌가 없으면 계좌 생성 안내 화면 표시
- 계좌는 거래 데이터의 상위 개념으로 동작
- 거래 생성 과정에서 선택적으로 영수증 파일 첨부 가능
- 누적된 거래 데이터는 대시보드에서 요약 형태로 제공

### 2.5 설계 의도

화면 구성은 UI 중심이 아니라 사용자 행동 흐름 기준으로 정의한다. 데이터 소유권 기준으로 계좌 → 거래 → 영수증 순서의 계층 구조를 가진다.

---

## 3. 시스템 아키텍처

### 3.1 전체 구성도 (서버 렌더링 중심 MVT)

```
[Browser]
   │  GET /transactions/
   ▼
[urls.py]
   │
   ▼
[TransactionListView]
   │
   ▼
[Transaction.objects.filter(user=request.user)]
   │
   ▼
[PostgreSQL DB]
   │
   ▼
[transactions/transaction_list.html]
   │
   ▼
[Browser]
```

- URL → View 매핑 처리
- View가 요청의 중심 역할 수행
- Model은 데이터 처리 및 비즈니스 로직 담당
- Template은 화면 렌더링 전담
- 서버에서 HTML을 생성하여 응답 반환

### 3.2 클래스 기반 요청 흐름 (거래 생성 예시)

```
[POST /transactions/create/]
        │
        ▼
urls.py
(path: "create/")
        │
        ▼
transactions/views.py
TransactionCreateView (CreateView)
        │
        ▼
TransactionForm.clean_amount()
(입력 검증: 금액 > 0, 최대 100억)
        │
        ▼
TransactionCreateView.form_valid()
(user 자동 설정 + 영수증 업로드 처리)
        │
        ▼
transactions/models.py
Transaction.save()
(계좌 잔액 자동 업데이트)
        │
        ▼
HttpResponseRedirect
        │
        ▼
[GET /transactions/]
TransactionListView
```

---

## 4. 데이터베이스 설계

### 4.1 ERD

- Lucidchart로 ERD 작성 (PK/FK, Cardinality 표기)
- 첨부: ERD 이미지 1장

### 4.2 ERD 관계 요약

```
- User    1 : N  Account
- User    1 : N  Transaction
- User    1 : N  Category
- Account 1 : N  Transaction
- Category 1 : N  Transaction
- Transaction 1 : 1  Attachment (MVP 기준: 거래당 영수증 1개)
```

### 4.3 제약조건 설계 (무결성 규칙)

models.py 기준 데이터 무결성 규칙:

| 항목 | 제약 내용 |
|------|----------|
| amount | 0.01 이상만 허용 (`MinValueValidator(Decimal('0.01'))`) |
| tx_type | IN / OUT 값으로 제한 (`choices`) |
| occurred_at | 필수 값 (null 미허용) |
| account_number | 숫자와 하이픈만 허용, 최소 8자리 |
| balance | 0 이상만 허용 (폼 검증) |
| Attachment | Transaction과 1:1 관계 (`OneToOneField`) |
| category | 삭제 시 NULL 처리 (`SET_NULL`) |
| account/transaction | 사용자 삭제 시 CASCADE 삭제 |

### 4.4 인덱스 설계 (조회 패턴 기반)

주요 조회 패턴:

- 사용자 기준 거래 목록 조회 빈도 높음
- 거래일시 기준 정렬/필터 사용
- 계좌 기준 거래 필터 사용

적용 인덱스:

| 대상 | 인덱스 | 근거 |
|------|--------|------|
| Transaction.occurred_at | `models.Index(fields=['-occurred_at'])` | 거래일 기준 정렬 최적화 |
| Transaction.user_id | FK 자동 인덱스 | 사용자별 거래 조회 |
| Transaction.account_id | FK 자동 인덱스 | 계좌별 거래 필터 |
| Transaction.category_id | FK 자동 인덱스 | 카테고리별 필터 |

### 4.5 Data Dictionary

#### 4.5.1 Transaction 테이블 (핵심)

| 컬럼 | 타입 | Null | 설명 | 예시 |
|------|------|-----:|------|------|
| id | bigint | N | PK | 101 |
| user_id | FK (User) | N | 소유자 | 3 |
| account_id | FK (Account) | N | 계좌 | 7 |
| category_id | FK (Category) | Y | 카테고리 | 2 |
| tx_type | varchar(3) | N | IN/OUT | OUT |
| amount | decimal(12,2) | N | 금액 (0.01 이상) | 12000.00 |
| occurred_at | datetime | N | 거래일시 | 2026-02-01 |
| merchant | varchar(100) | Y | 가맹점/거래처 | 스타벅스 |
| memo | text | Y | 메모 | 아메리카노 2잔 |
| created_at | datetime | N | 생성일 (자동) | 2026-02-01 |
| updated_at | datetime | N | 수정일 (자동) | 2026-02-01 |

#### 4.5.2 Account 테이블

| 컬럼 | 타입 | Null | 설명 | 예시 |
|------|------|-----:|------|------|
| id | bigint | N | PK | 7 |
| user_id | FK (User) | N | 소유자 | 3 |
| name | varchar(100) | N | 계좌명 | 생활비 통장 |
| bank_name | varchar(50) | N | 은행명 | 국민은행 |
| account_number | varchar(50) | N | 계좌번호 | 110-123-456789 |
| balance | decimal(12,2) | N | 잔액 (기본값 0) | 150000.00 |
| is_active | boolean | N | 활성 여부 | True |
| created_at | datetime | N | 생성일 (자동) | 2026-01-15 |
| updated_at | datetime | N | 수정일 (자동) | 2026-02-01 |

#### 4.5.3 Attachment 테이블

| 컬럼 | 타입 | Null | 설명 | 예시 |
|------|------|-----:|------|------|
| id | bigint | N | PK | 1 |
| user_id | FK (User) | N | 업로더 | 3 |
| transaction_id | FK (Transaction, 1:1) | N | 거래 | 101 |
| file | FileField | N | 파일 경로 | receipts/2026/02/01/img.jpg |
| original_name | varchar(255) | N | 원본 파일명 | 영수증.jpg |
| size | integer | N | 파일 크기(bytes) | 245000 |
| content_type | varchar(100) | N | 파일 타입 | image/jpeg |
| uploaded_at | datetime | N | 업로드일 (자동) | 2026-02-01 |

#### 4.5.4 Category 테이블

| 컬럼 | 타입 | Null | 설명 | 예시 |
|------|------|-----:|------|------|
| id | bigint | N | PK | 2 |
| user_id | FK (User) | Y | 생성자 (NULL: 공통) | 3 |
| name | varchar(50) | N | 카테고리명 | 식비 |
| type | varchar(4) | N | IN/OUT/BOTH | OUT |
| created_at | datetime | Y | 생성일 (자동) | 2026-01-20 |

---

## 5. 핵심 기능 구현 상세

views.py 기준으로 무엇을 구현했는지와 어떤 기준으로 동작하는지를 설명한다.

### 5.1 인증 (회원가입 / 로그인 / 로그아웃)

| 항목 | 내용 |
|------|------|
| 인증 방식 | Django 기본 인증 (django.contrib.auth) |
| 회원가입 | UserCreationForm 기반, username / password |
| 로그인 | AuthenticationForm 기반, 세션 로그인 |
| 로그아웃 | POST 요청, 세션 종료 |
| 접근 제어 | LoginRequiredMixin으로 로그인 필수 페이지 제한 |
| 홈 분기 | 로그인 O → 대시보드, 로그인 X → 로그인 페이지 |

Django 기본 인증 시스템을 사용하여 회원가입, 로그인, 로그아웃 기능을 구현하였다. 로그인하지 않은 사용자는 계좌/거래 관련 페이지에 접근할 수 없도록 제한하였다.

### 5.2 계좌 CRUD

| 기능 | 설명 |
|------|------|
| 계좌 생성 | 계좌명, 은행명, 계좌번호, 초기 잔액 입력 |
| 계좌 조회 | 로그인한 사용자 본인의 활성 계좌만 조회 |
| 계좌 수정 | 계좌명, 은행명, 계좌번호, 잔액 수정 |
| 계좌 삭제 | 비활성 처리 (is_active=False) |
| 총 수입/지출 | 계좌 목록에서 전체 수입/지출/순자산 요약 표시 |

##### 계좌번호 마스킹 정책

| 항목 | 내용 |
|------|------|
| 저장 방식 | 전체 계좌번호 DB 저장 |
| 출력 방식 | 중간 부분 마스킹 처리 |
| 예시 | `110-123-456789` → `110-***-6789` |
| 구현 위치 | Account 모델의 `masked_account_number` 프로퍼티 |

계좌번호는 DB에 전체 저장되지만, 화면과 관리자 페이지에서는 중간 부분을 마스킹하여 표시한다.

### 5.3 거래 CRUD

| 기능 | 설명 |
|------|------|
| 거래 생성 | 입금/출금 거래 등록, 계좌 잔액 자동 반영 |
| 거래 조회 | 사용자별 거래 목록/상세 (활성 계좌 거래만) |
| 거래 수정 | 금액, 날짜, 메모 수정, 잔액 자동 재계산 |
| 거래 삭제 | 거래 기록 삭제, 잔액 자동 복원 |

##### 입력 검증 정책

| 항목 | 검증 내용 |
|------|----------|
| 계좌 선택 | 로그인한 사용자의 활성 계좌만 선택 가능 |
| 금액 | 0보다 큰 값만 허용, 최대 100억 제한 |
| 거래 유형 | IN / OUT 중 하나 |
| 거래일 | 필수 입력 (datetime-local) |
| 카테고리 | 거래 유형에 맞는 카테고리만 표시 (IN→수입/공통, OUT→지출/공통) |

거래 생성 및 수정 시, 선택 가능한 계좌는 로그인한 사용자의 활성 계좌로 제한하였다. 거래 저장/수정/삭제 시 계좌 잔액이 자동으로 반영된다.

### 5.4 거래 필터 / 검색 / 정렬 (request.GET 기반)

| 구분 | 내용 | 쿼리 파라미터 |
|------|------|-------------|
| 기간 필터 | 시작일 ~ 종료일 | `start_date`, `end_date` |
| 계좌 필터 | 특정 계좌 선택 | `account` |
| 카테고리 필터 | 거래 분류 | `category` |
| 거래 유형 | 입금 / 출금 | `tx_type` |
| 검색 | 메모, 가맹점 키워드 | `q` |
| 정렬 | 최신 거래 순 기본 | `-occurred_at` |
| 페이지네이션 | 페이지당 20건 | `paginate_by=20` |

거래 목록은 JavaScript 없이, `request.GET` 쿼리스트링을 이용하여 서버에서 필터링 및 정렬을 수행한다.

예시 URL:
```
/transactions/?account=1&category=2&tx_type=OUT&q=카페&start_date=2026-01-01&end_date=2026-01-31
```

### 5.5 영수증 파일 업로드

| 항목 | 내용 |
|------|------|
| 업로드 대상 | 거래(Transaction) 단위 |
| 허용 파일 | jpg, jpeg, png, pdf |
| 파일 수 | 거래당 1개 (OneToOneField) |
| 저장 위치 | `media/receipts/YYYY/MM/DD/` |
| 삭제 | 거래 상세 화면에서 가능, 실제 파일도 함께 삭제 |

##### 파일 검증 정책

| 항목 | 내용 |
|------|------|
| 확장자 | .jpg, .jpeg, .png, .pdf |
| 용량 제한 | 5MB 이하 |
| 이미지 검증 | PIL(Pillow)로 실제 이미지 파일 여부 확인 |

영수증 파일은 MEDIA 디렉토리에 날짜별 하위 폴더로 저장되며, 업로드 시 확장자, 용량, 이미지 유효성을 검증하여 잘못된 파일 업로드를 방지하였다.

### 5.6 대시보드 요약

| 구분 | 내용 |
|------|------|
| 월별 요약 | 총수입 / 총지출 / 순합(계좌 잔액 합계) |
| 카테고리별 | 지출 Top 5 합계 및 비율 |
| 달력 | 날짜별 수입/지출 표시 |
| 최근 거래 | 최대 4건 표시 |
| 계좌 필터 | 특정 계좌 기준 통계 가능 |
| 월 변경 | 쿼리스트링 기반 (`?month=2026-02`) |

대시보드는 선택한 월을 기준으로 거래 데이터를 집계하여 월별 수입/지출 현황과 카테고리별 소비 내역을 표시한다. 계좌가 없는 사용자에게는 계좌 생성 안내 화면을 제공한다.

예시 URL:
```
/dashboard/?month=2026-02&account=1
```

---

## 6. 보안 및 권한 설계

### 6.1 LoginRequired 정책

- 계좌 / 거래 / 대시보드 / 카테고리 화면에 로그인 필수 정책 적용
- 비인증 사용자 요청 차단
- 인증 실패 시 로그인 화면으로 리디렉션 (`LOGIN_URL = '/login/'`)
- 적용 방식: `LoginRequiredMixin` (클래스 기반 뷰), `@login_required` (함수 기반 뷰)

### 6.2 QuerySet user 필터링 전략

| 화면 | 적용 방식 | 코드 위치 |
|------|----------|----------|
| 계좌 목록 | `Account.objects.filter(user=request.user, is_active=True)` | AccountListView |
| 거래 목록 | `Transaction.objects.filter(user=request.user)` | TransactionListView |
| 거래 상세/수정/삭제 | `Transaction.objects.filter(user=request.user)` | get_queryset() |
| 대시보드 | `Transaction.objects.filter(user=request.user)` | DashboardView |
| 카테고리 목록 | `Category.objects.filter(user=request.user)` | CategoryListView |

데이터 조회 시점에서 사용자 필터를 적용하여, 로그인한 사용자 본인의 데이터만 반환한다.

### 6.3 인증 / 접근 제어 요약 표

| 구분 | 적용 대상 | 적용 방식 | 설명 |
|------|----------|----------|------|
| 로그인 필수 | 계좌, 거래, 대시보드, 카테고리 | LoginRequiredMixin | 비인증 사용자 접근 제한 |
| 인증 상태 유지 | 전체 서비스 | Django Session Auth | 세션 기반 사용자 식별 |
| CSRF 보호 | 상태 변경 요청 (POST) | CsrfViewMiddleware | 요청 위조 공격 방지 |
| 로그아웃 | 사용자 세션 | django.contrib.auth.logout | 세션 무효화 |
| 비밀번호 검증 | 회원가입 | 4가지 Validator 적용 | 유사성/최소길이/일반비밀번호/숫자전용 검증 |

인증 및 접근 제어는 Django 세션 인증 및 로그인 필수 정책을 기준으로 구성한다.

### 6.4 객체 접근 404 전략

- 상세/수정/삭제 요청 시 `get_queryset()`에서 객체 소유자 검증 수행
- 본인 소유 데이터만 접근 허용
- 타 사용자 소유 데이터 요청은 404 응답으로 처리 (리소스 존재 은닉)

적용 대상:

| View | 접근 제어 방식 |
|------|-------------|
| AccountDetailView | `get_queryset()` → `filter(user=request.user)` |
| AccountUpdateView | `get_queryset()` → `filter(user=request.user)` |
| AccountDeleteView | `get_queryset()` → `filter(user=request.user)` |
| TransactionDetailView | `get_queryset()` → `filter(user=request.user)` |
| TransactionUpdateView | `get_queryset()` → `filter(user=request.user)` |
| TransactionDeleteView | `get_queryset()` → `filter(user=request.user)` |
| CategoryDeleteView | `get_queryset()` → `filter(user=request.user)` |
| AttachmentUploadView | `get_object_or_404(Transaction, pk=pk, user=request.user)` |
| AttachmentDeleteView | `get_object_or_404(Attachment, pk=pk, user=request.user)` |

403(권한 없음)이 아닌 404를 사용하여, 타 사용자에게 리소스 존재 여부 자체를 노출하지 않는 전략이다.

적용 확인 방법:
1. 일반 창 → 사용자 A로 로그인
2. 시크릿 창 → 사용자 B로 로그인
3. 사용자 A 거래 URL (예: `/transactions/5/`)을 사용자 B에서 접속
4. 404 Not Found 응답 확인

### 6.5 CSRF 보호 동작

- Django 미들웨어 `CsrfViewMiddleware` 활성화
- 상태 변경 요청(POST)에 CSRF 보호 적용
- 템플릿 폼 요청 시 `{% csrf_token %}` 포함
- AJAX 요청(카테고리 생성)에도 CSRF 토큰 전달
- 토큰 검증 실패 시 요청 거부 (403)

### 6.6 민감정보 마스킹 정책

| 항목 | 마스킹 대상 | 표기 형식 | 적용 위치 |
|------|-----------|----------|----------|
| 계좌번호 | 중간 자릿수 | `110-***-6789` | 화면 출력 + Admin |
| 비밀번호 | 전체 | 해시 저장 (PBKDF2) | Django 기본 |

- 계좌번호 마스킹은 `Account.masked_account_number` 프로퍼티로 구현
- Admin 페이지에서도 `masked_account_display` 메서드로 마스킹 표시

### 6.7 세션 증빙 (브라우저 쿠키 확인)

확인 절차:
1. 로그인 완료 상태에서 DevTools 열기
2. Application → Cookies 확인

확인 대상:
```
sessionid    - 세션 식별 쿠키
csrftoken    - CSRF 보호 토큰
```

캡처 체크리스트:
- [ ] 로그인 완료 상태 화면
- [ ] DevTools → Cookies → `sessionid` 표시
- [ ] URL 포함 화면 캡처

### 보안 설계 요약 (체크리스트)

| 항목 | 적용 여부 |
|------|:---------:|
| 로그인 필수 페이지 분리 | ✅ |
| 본인 데이터만 조회 가능 | ✅ |
| URL 직접 접근 차단 (404) | ✅ |
| CSRF 보호 | ✅ |
| 비밀번호 해시 저장 | ✅ |
| 민감정보 마스킹 | ✅ |
| 비밀번호 강도 검증 (4종) | ✅ |

---

## 7. 관리자 페이지(Admin) 활용

### 7.1 Admin 도입 목적

서비스 화면(UI)에서 제공하지 않는 관리 기능을 관리자 페이지에서 대체한다.

### 7.2 Admin 사용 시나리오

| 시나리오 | 관리자에서 하는 일 | 기대 효과 |
|---------|-----------------|----------|
| 테스트 데이터 생성 | 계좌/거래/카테고리 생성 | 개발 속도 향상 |
| 데이터 이상 확인 | 거래 금액/날짜/계좌 연결 확인 | 오류 원인 파악 |
| 운영성 점검 | 사용자/계좌/거래 관계 확인 | 데이터 무결성 확인 |
| 카테고리 관리 | 공통 카테고리 추가/수정/삭제 | 사용자 UI 단순화 |

### 7.3 admin.py 커스터마이징 포인트

Admin은 "전체 목록을 보기 좋게" 만드는 것이 핵심이며, MVP에서는 다음 커스터마이징을 적용하였다:
- 컬러 뱃지: 거래 유형(입금: 초록, 출금: 빨강) 시각적 표시
- 금액 컬러링: 입금(+초록), 출금(-빨강) 색상 + 굵은 글씨
- 날짜 계층: `date_hierarchy`로 날짜 네비게이션 제공
- 쿼리 최적화: `select_related`로 관련 데이터 미리 로딩
- fieldsets: 기본 정보 / 거래 정보 / 생성/수정 정보 섹션 분리

### 7.4 모델별 Admin 설정 요약 표

| 모델 | list_display | list_filter | search_fields |
|------|-------------|-------------|---------------|
| Account | user, name, bank_name, 계좌번호(마스킹), balance, is_active, created_at | is_active, bank_name, created_at | name, bank_name, user__username |
| Transaction | occurred_at, user, account, 유형(뱃지), 금액(컬러), category, merchant | tx_type, category, occurred_at, created_at | user__username, account__name, merchant, memo |
| Category | name, type(뱃지) | type | name |

### 7.5 관리자 권한 정책

| 항목 | 정책 |
|------|------|
| 접근 경로 | `/admin/` |
| 접근 가능 대상 | superuser만 |
| 일반 사용자 | 접근 불가 |
| 계정 생성 | `createsuperuser`로 생성 |
| 비 superuser 거래 조회 | 본인 거래만 표시 |

Admin은 운영자 전용 기능이므로, `superuser`만 접근하도록 제한하였다. 일반 사용자 계정은 관리자 페이지에 접근할 수 없다. 비 superuser가 Admin에 접근하더라도 본인 거래만 조회 가능하도록 `get_queryset`을 재정의하였다.

### 7.6 민감정보 노출 최소화 (운영 화면 기준)

민감정보(계좌번호)는 운영 화면에서도 노출 최소화를 위해 `masked_account_display` 메서드로 마스킹하여 표시하도록 처리하였다. Admin의 `readonly_fields`에 마스킹 필드를 추가하여 편집 화면에서도 마스킹된 번호가 표시된다.

---

## 8. 테스트 및 CI (GitHub Actions)

### 8.1 테스트 범위 요약

| 구분 | 테스트 대상 | 확인 내용 |
|------|-----------|----------|
| 모델 | Account 생성/마스킹/정렬 | 모델 동작 및 프로퍼티 검증 |
| 모델 | Transaction 잔액 연동 | 생성/수정/삭제 시 잔액 자동 반영 |
| 모델 | Category 생성/타입 | 카테고리 기본값 및 사용자 연결 |
| 폼 | AccountForm 검증 | 계좌번호 형식, 잔액 음수 제한 |
| 폼 | TransactionForm 검증 | 금액 0 이하/100억 초과 제한, 카테고리 필터 |
| 인증/권한 | 로그인 여부 | 비로그인 시 접근 차단 (302) |
| 인증/권한 | 사용자 구분 | 타 사용자 데이터 접근 차단 (404) |
| 계좌 CRUD | 생성/조회/수정/삭제 | 본인 계좌만 처리 가능 |
| 거래 CRUD | 생성/조회/수정/삭제 | 본인 거래만 처리 가능 |
| 필터/검색 | 기간/계좌/타입/키워드 | 정상 필터링 여부 |
| 카테고리 API | 타입별 필터링 | IN/OUT/전체 반환 검증 |
| 대시보드 | 통계/필터/권한 | 수입/지출 집계, 월 필터, 타 사용자 데이터 미포함 |

실제 서비스 운영을 가정하여, 사용자 데이터 분리와 주요 CRUD 기능 위주로 테스트 범위를 선정하였다.

### 8.2 테스트 실행 방법

| 항목 | 내용 |
|------|------|
| 실행 명령어 | `python manage.py test` |
| 실행 대상 | accounts, transactions, dashboard 앱 전체 |
| 테스트 DB | Django 테스트용 임시 DB (자동 생성/제거) |
| 테스트 러너 | Django 기본 테스트 러너 |

로컬 환경에서는 Django 기본 테스트 러너를 사용하여 테스트를 실행한다. 테스트 실행 시 별도의 테스트용 데이터베이스가 생성되며, 테스트 종료 후 자동으로 제거된다.

### 8.3 CI 동작 조건

| 이벤트 | CI 동작 |
|--------|---------|
| workflow_dispatch | 수동 실행 (현재 설정) |
| Push (main) | 배포 자동 실행 (비활성화 상태, 주석 처리) |

현재 CI는 Fly.io 배포 워크플로우로 구성되어 있으며, 로컬 발표 기간 중 수동 실행만 가능하도록 설정하였다.

### 8.4 CI 파이프라인 흐름

```
코드 Push / 수동 트리거
        ↓
GitHub Actions 실행
        ↓
Ubuntu 환경 준비
        ↓
코드 Checkout
        ↓
Fly CLI 설치
        ↓
flyctl deploy --remote-only
        ↓
Docker 빌드 (Dockerfile)
        ↓
마이그레이션 실행 (release_command)
        ↓
Gunicorn 서버 실행
        ↓
배포 완료
```

### 8.5 CI 구성 요약 표

| 단계 | 내용 |
|------|------|
| OS | Ubuntu (latest) |
| 배포 도구 | Fly CLI (flyctl) |
| 빌드 | Docker (Python 3.12-slim) |
| 패키지 설치 | requirements.txt |
| Static 수집 | collectstatic --noinput |
| 마이그레이션 | migrate --noinput (deploy 시 자동) |
| 서버 | Gunicorn (workers=2) |
| 결과 확인 | GitHub Actions 로그 |

### 8.6 CI 결과 확인 위치

- GitHub 저장소 → Actions 탭 → Fly Deploy 워크플로우
- 배포 성공/실패 로그 확인 가능

---

## 9. 배포 및 환경 분리

### 9.1 배포 여부 및 플랫폼

- 배포 플랫폼: Fly.io
- 앱 이름: `accountbook-project`
- 리전: `sin` (싱가포르)

### 9.2 배포 목적

- 로컬 환경이 아닌 실제 서버 환경에서 Django 애플리케이션 실행 경험
- 환경변수 기반 설정 분리 연습
- Docker 컨테이너 배포 경험

### 9.3 환경 구성 요약 표

| 구분 | 개발 환경 (Local) | 배포 환경 (Fly.io) |
|------|-------------------|-------------------|
| 실행 위치 | 로컬 PC | Fly.io 서버 (Docker) |
| Python | 3.10 | 3.12 |
| DEBUG | True | False |
| DB | PostgreSQL (Local) | PostgreSQL (Fly.io) |
| SECRET_KEY | 로컬 .env | Fly.io Secrets |
| MEDIA | 로컬 media/ 디렉토리 | Fly.io 스토리지 |
| Static | Django 개발 서버 | WhiteNoise + collectstatic |
| 서버 | `manage.py runserver` | Gunicorn (2 workers) |
| 접근 URL | `localhost:8000` | `accountbook-project.fly.dev` |

개발 환경과 배포 환경은 동일한 코드베이스를 사용하되, 실행 환경에 따라 설정 값만 다르게 적용되도록 구성하였다.

### 9.4 환경변수 관리

##### 9.4.1 로컬 개발 환경 (.env)

| 변수명 | 설명 |
|--------|------|
| SECRET_KEY | Django 비밀키 |
| DB_NAME | 데이터베이스 이름 |
| DB_USER | DB 사용자 |
| DB_PASSWORD | DB 비밀번호 |
| DB_HOST | DB 호스트 |
| DB_PORT | DB 포트 |

로컬 개발 환경에서는 `.env` 파일과 `python-dotenv`를 사용하여 환경변수를 관리하였다. `.env` 파일은 Git에 포함되지 않도록 `.gitignore`에 등록하였다.

##### 9.4.2 배포 환경 (Fly.io Secrets)

- `fly secrets set` 명령어를 사용하여 서버 환경변수 등록
- 코드에는 실제 값이 노출되지 않음
- `FLY_API_TOKEN`은 GitHub Secrets에 등록하여 CI에서 사용

Fly.io 배포 환경에서는 Secrets 기능을 사용하여 환경변수를 관리하였다. 이를 통해 배포 서버에만 필요한 민감 정보가 안전하게 저장된다.

### 9.5 DEBUG 설정 분리

| 환경 | DEBUG 값 | 이유 |
|------|----------|------|
| 개발 | True | 오류 확인 및 디버깅 |
| 배포 | False | 보안 및 안정성 |

배포 환경에서는 DEBUG를 False로 설정하여 상세 오류 정보가 외부에 노출되지 않도록 하였다.

### 9.6 실행 방법 (3분 가이드)

##### 9.6.1 로컬 실행 절차

```bash
# 1. 가상환경 활성화
source venv/bin/activate

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 환경변수 설정
# .env 파일 생성 후 SECRET_KEY, DB 정보 입력

# 4. 마이그레이션
python manage.py migrate

# 5. 서버 실행
python manage.py runserver
```

##### 9.6.2 배포 실행 절차

```
로컬 코드 준비
      ↓
fly launch / fly deploy
      ↓
환경변수(secrets) 설정
      ↓
Docker 빌드 (Python 3.12 + requirements.txt)
      ↓
collectstatic 실행
      ↓
migrate 실행 (release_command)
      ↓
Gunicorn 서버 시작
      ↓
accountbook-project.fly.dev 접속
```

배포는 Fly.io CLI를 통해 수행되며, 코드 변경 후 `fly deploy` 명령어로 재배포할 수 있다.

---

## 10. Git 브랜치/PR 전략

### 10.1 브랜치 규칙

| 브랜치 | 용도 |
|--------|------|
| `main` | 항상 배포 가능한 상태 유지 |
| `dev` | 개발 통합 브랜치 |
| `feature/*` | 기능 개발 및 수정 |

### 10.2 브랜치 네이밍 규칙

실제 사용된 브랜치:
- `feature/accounts` - 계좌 기능 개발
- `feature/transactions` - 거래 기능 개발
- `feature/dashboard` - 대시보드 기능 개발
- `feature/frontend` - 프론트엔드 작업
- `deploy-prod` - 배포용 브랜치

main 브랜치에는 직접 커밋하지 않고, PR을 통해 병합한다.

### 10.3 작업 흐름 (Workflow)

```
이슈 확인
   ↓
feature 브랜치 생성
   ↓
작업 & 커밋
   ↓
PR 생성
   ↓
리뷰 (셀프 또는 팀)
   ↓
main 브랜치 병합
```

모든 작업은 `feature/*` 브랜치에서 수행하고, 작업 완료 후 Pull Request를 통해 `main` 브랜치로 병합한다.

### 10.4 커밋 메시지 규칙

##### 타입 정의 표

| 타입 | 의미 | 사용 시점 |
|------|------|----------|
| feat | 기능 추가 | 새로운 API, 화면, 기능 |
| fix | 버그 수정 | 오류 해결, 잘못된 동작 수정 |
| refactor | 리팩토링 | 동작 변화 없이 구조 개선 |
| docs | 문서 변경 | README, 주석, 가이드 |
| test | 테스트 코드 | 테스트 추가/수정 |
| chore | 잡작업 / 설정 | 패키지, 환경설정, 정리 |
| style | 코드 스타일 | 공백, 포맷팅 (로직 변화 없음) |

##### 프로젝트 실제 커밋 메시지 예시

```
feat: 카테고리 관리/삭제 기능 추가 및 입력 폼 버튼 레이아웃 개선
feat: 거래 모델 완성 및 팀 협업을 위한 .env.example 추가
feat: dashboard 앱 완성
fix: 대시보드 순합 표시 수정 (balance)
fix: 카테고리 생성 후 거래 타입(IN/OUT) 유지되도록 수정
fix: 날아간 가계부 필터링 기능 복구 및 코드 최적화
refactor: Attachment 모델 통합
chore: 최종 명단 정리 및 이니셜 제거 확인
style: 카테고리 사용자 정의 기능 추가 및 설계도 정리
```

커밋 메시지는 "무엇을 했는지 한눈에 알 수 있도록" 작성한다.

### 10.5 충돌 처리 원칙

| 상황 | 기준 |
|------|------|
| 기능 개발 중 | rebase 사용 |
| PR 병합 시 | merge 사용 |
| 충돌 발생 | feature 브랜치에서 해결 |

충돌은 feature 브랜치에서 먼저 해결한 뒤 PR을 업데이트한다. main 브랜치에서는 충돌을 직접 수정하지 않는다.

---

## 11. 트러블슈팅 및 배운 점

### 11.1 주요 이슈 요약 (TOP 3)

| No | 이슈 | 영향 |
|----|------|------|
| 1 | 권한 누락으로 타 사용자 데이터 노출 가능성 | 보안 위험 |
| 2 | 파일 업로드 경로 및 검증 오류 | 기능 실패 |
| 3 | PostgreSQL 연결 및 마이그레이션 오류 | 서버 실행 불가 |

### 11.2 이슈별 해결 과정

##### 11.2.1 권한 누락으로 타 사용자 데이터 노출 가능성

| 단계 | 내용 |
|------|------|
| 문제 상황 | 거래 상세 URL을 직접 입력하면 타 사용자 데이터 접근 가능 |
| 원인 분석 | QuerySet 필터링만 적용하고, 객체 단위 접근 검증 누락 |
| 시도 | 목록 조회에 user 필터 추가 |
| 해결 | 상세/수정/삭제 View의 `get_queryset()`에서 user 필터 적용, 불일치 시 404 처리 |
| 결과 | 타 사용자 데이터 접근 완전 차단 |

조회 단계뿐 아니라 객체 접근 단계에서도 권한 검증이 필요함을 인지했다.

##### 11.2.2 파일 업로드 검증/경로 문제

| 단계 | 내용 |
|------|------|
| 문제 상황 | 업로드 파일이 저장되지 않거나 경로 오류 발생 |
| 원인 분석 | MEDIA_ROOT / MEDIA_URL 설정 누락 |
| 시도 | 파일 저장 경로 하드코딩 |
| 해결 | Django 기본 MEDIA 설정 사용 + AttachmentForm에서 확장자/용량/이미지 유효성 검증 |
| 결과 | 정상 업로드 및 조회 가능 |

파일 업로드는 경로 설정과 검증을 함께 고려해야 안정적으로 동작한다.

##### 11.2.3 PostgreSQL 연결/마이그레이션 문제

| 단계 | 내용 |
|------|------|
| 문제 상황 | migrate 실행 시 DB 연결 오류 |
| 원인 분석 | 환경변수 누락 및 권한 설정 오류 |
| 시도 | settings.py 직접 수정 |
| 해결 | python-dotenv 기반 .env 파일 환경변수 분리 |
| 결과 | 로컬/배포 환경 동일 구조 유지 |

DB 설정은 코드가 아니라 환경변수로 관리해야 재사용과 배포가 쉬워진다.

### 11.3 배운 점 요약

| 구분 | 배운 점 |
|------|--------|
| 설계 | 기능보다 먼저 "데이터 소유 기준"을 정해야 한다 |
| 보안 | 로그인 ≠ 권한, 객체 단위 접근 검증이 필수 |
| 구현 | 파일 업로드는 검증/경로/용량을 함께 고려해야 한다 |
| 테스트 | 수동 테스트만으로는 보안 이슈를 놓치기 쉽다 |
| 개발 습관 | 환경 분리와 문서화가 문제 해결을 빠르게 한다 |

이번 프로젝트를 통해 기능 구현뿐 아니라, 권한 설계·환경 분리·테스트 습관의 중요성을 경험할 수 있었다. 향후 프로젝트에서는 초기 설계 단계에서부터 이러한 요소를 함께 고려할 예정이다.

---

## 12. 결론 및 개선 방향

### 12.1 현재 한계 (MVP 제약)

- 서버 렌더링 방식으로 프론트엔드 분리 미적용
- JavaScript 최소 사용 (카테고리 AJAX만)
- JWT 미적용, 세션 기반 인증만 구현
- 파일 업로드 로컬/서버 스토리지만 사용 (S3 미연동)
- 모니터링/로깅 시스템 미구축
- API 문서화 미적용

### 12.2 개선 로드맵 (다음 단계)

| 단계 | 내용 | 기대 효과 |
|------|------|----------|
| DRF API 분리 | Django REST Framework 기반 API 서버 구성 | 프론트/백엔드 독립 |
| JWT 인증 | Token 기반 인증 전환 | 무상태 인증, 모바일 지원 |
| 프론트 분리 (React) | SPA 방식 프론트엔드 구현 | UX 개선, 비동기 처리 |
| 모니터링 | Prometheus / Grafana 연동 | 성능 지표 수집 및 시각화 |
| 파일 스토리지 | AWS S3 연동 | 안정적 파일 관리 |
| CI 강화 | 테스트 자동 실행 + 코드 품질 검사 | 배포 안정성 향상 |

---

## 13. README 구성

### 13.1 README 목적

README는 개발자 / 면접관 / 협업자 / 미래의 나 자신을 위한 문서이다. "이 프로젝트가 무엇인지 + 어떻게 실행하는지"를 가장 빠르게 전달하는 역할을 한다.

### 13.2 README 필수 섹션

##### 13.2.1 프로젝트 소개

```
서버 렌더링 기반 Django 웹 애플리케이션으로,
사용자의 계좌 및 거래 내역을 기록하고 요약 정보를 제공하는 개인 가계부 서비스
```

##### 13.2.2 주요 기능

- 사용자 인증 (회원가입 / 로그인 / 로그아웃)
- 계좌 CRUD (생성 / 조회 / 수정 / 삭제)
- 거래 CRUD
- 거래 필터 / 검색 / 정렬
- 영수증 파일 업로드
- 월별 대시보드 요약

##### 13.2.3 기술 스택

- Backend: Django 4.2
- Database: PostgreSQL
- Frontend: Django Template (Server Rendering)
- Deployment: Fly.io (Docker + Gunicorn)

##### 13.2.4 로컬 실행 방법

```bash
source venv/bin/activate
pip install -r requirements.txt
# .env 파일 생성
python manage.py migrate
python manage.py runserver
```

##### 13.2.5 환경변수 (.env)

```env
SECRET_KEY=your_secret_key
DB_NAME=accountbook
DB_USER=postgres
DB_PASSWORD=*****
DB_HOST=localhost
DB_PORT=5432
```

`.env` 파일은 Git에 포함되지 않으며 `.gitignore`로 관리한다.

##### 13.2.6 디렉토리 구조

```
accountbook_project/
 ├─ settings.py
 ├─ urls.py
 └─ wsgi.py

accounts/          # 인증 + 계좌 관리
 ├─ models.py      # Account 모델
 ├─ views.py       # 인증 + 계좌 CRUD View
 ├─ forms.py       # AccountForm
 ├─ admin.py       # AccountAdmin
 └─ templates/accounts/

transactions/      # 거래 + 카테고리 + 영수증
 ├─ models.py      # Transaction, Category, Attachment
 ├─ views.py       # 거래 CRUD + 필터 + 영수증 View
 ├─ forms.py       # TransactionForm, AttachmentForm, CategoryForm
 ├─ admin.py       # TransactionAdmin, CategoryAdmin
 └─ templates/transactions/

dashboard/         # 대시보드 + 영수증 관리
 ├─ views.py       # DashboardView + 영수증 업로드/삭제/다운로드
 └─ templates/dashboard/

templates/         # 공통 템플릿
 └─ base.html

static/            # CSS, JS
media/             # 업로드 파일 (영수증)
```

##### 13.2.7 화면 예시

- 계좌 목록
- 거래 목록
- 대시보드

(스크린샷 이미지 첨부)

##### 13.2.8 배포 주소

```
https://accountbook-project.fly.dev
```

##### 13.2.9 프로젝트 범위 고지

본 프로젝트는 학습 및 포트폴리오 목적의 MVP 구현 버전이다. 운영 환경 수준의 확장 기능 및 고급 보안 기능은 포함하지 않는다.

### 13.3 PDF 구성 팁 (페이지 배치 가이드)

- **페이지 1~2:** 요약 + 유저 플로우 + 아키텍처 그림
- **페이지 3~4:** ERD + 핵심 기능 (스크린샷 3~5장)
- **페이지 5:** 보안/권한 + Admin
- **페이지 6:** 테스트/CI + 배포/환경분리
- **페이지 7:** PR 전략 + 트러블슈팅 + 개선 로드맵
