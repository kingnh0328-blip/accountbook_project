# AccountBook 프로젝트

> 계좌 기반 거래 내역 관리 시스템 (Django + PostgreSQL)

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Django](https://img.shields.io/badge/Django-4.2-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![CI](https://github.com/your-username/accountbook/workflows/AccountBook%20CI/badge.svg)

## 📋 프로젝트 개요

로그인한 사용자가 여러 개의 계좌를 등록하고, 각 계좌에 대한 입출금 거래 내역을 기록·조회·수정·삭제하며, 
영수증 파일 업로드와 대시보드에서 월별/카테고리별 요약을 확인할 수 있는 Django 기반 웹 서비스입니다.

### 주요 기능

- ✅ **사용자 인증**: 회원가입, 로그인, 로그아웃
- ✅ **계좌 관리**: 계좌 CRUD, 계좌번호 마스킹
- ✅ **거래 관리**: 거래 CRUD, 필터링, 검색
- ✅ **영수증 관리**: 파일 업로드/조회/삭제
- ✅ **대시보드**: 월별 수입/지출 통계, 카테고리별 집계
- ✅ **관리자 페이지**: Django Admin 커스터마이징
- ✅ **보안**: 본인 데이터만 접근, 민감정보 마스킹

## 🏗️ 기술 스택

### Backend
- Python 3.11
- Django 4.2
- PostgreSQL 15

### Frontend
- Django Template (서버 사이드 렌더링)
- Bootstrap 5 (CSS Framework)
- No JavaScript (순수 HTML/CSS)

### DevOps
- GitHub Actions (CI)
- Fly.io (배포)

## 📊 ERD (Entity Relationship Diagram)

```
User (Django 기본 User)
 ├─ Account (1:N) - 계좌
 │    └─ Transaction (1:N) - 거래 내역
 │          ├─ Category (N:1) - 카테고리
 │          └─ Attachment (1:1) - 영수증 첨부파일
```

### 주요 모델

- **User**: Django 기본 인증 시스템
- **Account**: 계좌 정보 (통장, 카드, 현금 등)
- **Transaction**: 거래 내역 (입금/출금)
- **Category**: 거래 분류 (식비, 교통, 월세 등)
- **Attachment**: 영수증 파일

## 🚀 시작하기

### 1. 저장소 클론

```bash
git clone https://github.com/your-username/accountbook.git
cd accountbook
```

### 2. 가상환경 생성 및 활성화

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정

`.env` 파일을 프로젝트 루트에 생성:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_ENGINE=postgresql
DB_NAME=accountbook
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. PostgreSQL 설정

PostgreSQL을 설치하고 데이터베이스를 생성:

```bash
# PostgreSQL 접속
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE accountbook;
CREATE USER your_db_user WITH PASSWORD 'your_db_password';
GRANT ALL PRIVILEGES ON DATABASE accountbook TO your_db_user;
\q
```

### 6. 마이그레이션 적용

```bash
python manage.py migrate
```

### 7. 관리자 계정 생성

```bash
python manage.py createsuperuser
```

### 8. 카테고리 초기 데이터 로드 (선택)

```bash
python manage.py loaddata categories.json
```

### 9. 개발 서버 실행

```bash
python manage.py runserver
```

브라우저에서 `http://localhost:8000` 접속

## 📁 프로젝트 구조

```
accountbook/
├── accountbook/          # 프로젝트 설정
│   ├── settings.py      # Django 설정
│   ├── urls.py          # 메인 URL 라우팅
│   └── wsgi.py
├── accounts/            # 인증 및 계좌 관리 앱
│   ├── models.py        # Account 모델
│   ├── views.py         # 회원가입, 로그인, 계좌 CRUD
│   ├── forms.py         # 폼 정의
│   ├── urls.py          # URL 라우팅
│   └── templates/       # 템플릿
├── transactions/        # 거래 관리 앱
│   ├── models.py        # Transaction, Attachment 모델
│   ├── views.py         # 거래 CRUD, 필터링
│   ├── forms.py         # 폼 정의
│   └── templates/       # 템플릿
├── dashboard/           # 대시보드 앱
│   ├── views.py         # 통계 및 집계
│   └── templates/       # 대시보드 템플릿
├── static/              # 정적 파일 (CSS, JS)
├── media/               # 업로드 파일 (영수증)
├── templates/           # 공통 템플릿 (base.html)
├── .github/
│   └── workflows/
│       └── ci.yml       # GitHub Actions CI
├── requirements.txt     # Python 패키지 목록
├── .env                 # 환경변수 (Git 미포함)
├── .gitignore
└── README.md
```

## 🧪 테스트

### 전체 테스트 실행

```bash
python manage.py test
```

### 특정 앱 테스트

```bash
python manage.py test accounts
python manage.py test transactions
```

### 커버리지 확인 (pytest 사용 시)

```bash
pytest --cov=. --cov-report=html
```

## 🔐 보안

- **인증**: Django 기본 인증 시스템
- **권한**: 본인 데이터만 접근 가능 (QuerySet 필터링)
- **CSRF**: 모든 폼에 CSRF 토큰 적용
- **비밀번호**: Django 기본 해시 저장 (bcrypt)
- **민감정보 마스킹**: 계좌번호 화면/로그 제한
- **환경변수**: SECRET_KEY, DB 설정 분리

## 📱 주요 화면

### 1. 로그인 화면
![로그인](docs/screenshots/login.png)

### 2. 계좌 목록
![계좌 목록](docs/screenshots/accounts.png)

### 3. 거래 내역
![거래 내역](docs/screenshots/transactions.png)

### 4. 대시보드
![대시보드](docs/screenshots/dashboard.png)

## 🌐 배포

### Fly.io 배포

```bash
# Fly CLI 설치
curl -L https://fly.io/install.sh | sh

# 앱 생성
fly launch

# 배포
fly deploy
```

## 👥 팀원 및 역할

- **조장**: 프로젝트 총괄, ERD 설계, CI/CD 구축
- **팀원 A**: 인증 시스템, 계좌 관리
- **팀원 B**: 거래 관리, 필터링/검색
- **팀원 C**: 대시보드, 파일 업로드

## 📝 개발 일정

- **Day 1-2**: 프로젝트 세팅, ERD 설계
- **Day 3-4**: 인증 시스템, 계좌 관리
- **Day 5-6**: 거래 관리, 필터링
- **Day 7-8**: 파일 업로드, 대시보드
- **Day 9**: PostgreSQL 적용
- **Day 10**: 관리자 페이지, 테스트
- **Day 11**: CI 구축, 배포
- **Day 12**: 발표 준비

## 📄 라이선스

MIT License

## 🤝 기여

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 문의

프로젝트 관련 문의: your-email@example.com

---

**Made with ❤️ by AccountBook Team**