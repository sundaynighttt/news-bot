# News Bot 프로젝트 구조 설명

## 현재 구조 (2025년 5월 기준)

### 이중 구조 설명
현재 이 프로젝트는 **이중 구조**로 되어 있습니다:

```
google_upload/          # 🔙 기존 구조 (래퍼 스크립트)
└── *.py               # GitHub Actions가 실행하는 파일들
                       # 실제로는 src/ 폴더의 코드를 호출만 함

src/                   # ✨ 새로운 구조 (실제 코드)
├── scrapers/         # 뉴스 수집
├── processors/       # 요약 및 분석
├── uploaders/        # 데이터 업로드
└── utils/           # 공통 함수
```

### 왜 이중 구조인가?
1. GitHub Actions가 `google_upload/*.py`를 실행하도록 설정됨
2. 코드를 개선하면서 Actions 설정을 바꾸지 않기 위해 래퍼 사용
3. 래퍼는 단순히 `src/` 폴더의 실제 코드를 호출

### 실행 흐름
```
GitHub Actions → google_upload/news_scraper.py (래퍼)
                  ↓
                 src/scrapers/news_scraper.py (실제 코드)
```

### 향후 계획
- 안정화 후 GitHub Actions 수정
- 래퍼 스크립트 제거
- `src/` 구조만 유지

## 메인테이너를 위한 가이드

### 새로운 기능 추가할 때
1. 실제 코드는 `src/` 아래에 작성
2. 필요하면 `google_upload/`에 래퍼 추가
3. GitHub Actions는 래퍼 경로 사용

### 코드 수정할 때
- **실제 로직**: `src/` 폴더에서 수정
- **래퍼**: 건드리지 말 것 (단순 호출만)

### 디버깅할 때
```bash
# 로컬 테스트
python google_upload/스크립트명.py

# 실제 코드 위치
src/카테고리/스크립트명.py
```

## 나중에 단순화하기

### Step 1: Actions 파일 수정
```yaml
# 변경 전
run: python google_upload/news_scraper.py

# 변경 후  
run: python src/scrapers/news_scraper.py
```

### Step 2: 래퍼 제거
```bash
rm -rf google_upload/
```

### Step 3: 구조 단순화 완료
```
src/
├── scrapers/
├── processors/
├── uploaders/
└── utils/
```

---
마지막 업데이트: 2025년 5월 15일
