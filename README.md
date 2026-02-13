# 2026 Game Calendar

## 프로젝트 소개
이 프로젝트는 **오프라인 환경에서도 동작하는 게임 일정 캘린더 애플리케이션**입니다.
입력 데이터는 프로젝트 내 파일을 기준으로 읽어오며, 기본적으로 실행 디렉터리(프로젝트 루트) 아래의 입력 파일을 사용합니다.

- 예시 입력 파일 위치: `./data/`, `./input/` 또는 앱에서 지정한 상대 경로
- 네트워크 연결 없이 로컬 파일만으로 일정 조회/관리 가능

## 실행 방법
아래 순서로 로컬 실행 환경을 준비하고 앱을 실행합니다.

1. 가상환경 생성
   ```bash
   python -m venv .venv
   ```
2. 가상환경 활성화
   - macOS/Linux
     ```bash
     source .venv/bin/activate
     ```
   - Windows (PowerShell)
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
3. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```
4. 앱 실행
   ```bash
   python app.py
   ```

## 빌드 방법
배포용 실행 파일은 PyInstaller로 빌드합니다.

```bash
pyinstaller GameCalendar.spec
```

빌드가 완료되면 일반적으로 다음 경로에 산출물이 생성됩니다.

- 실행 파일(배포본): `dist/`
- 빌드 중간 산출물: `build/`

## 기능 요약
- **월 이동**: 이전/다음 월로 빠르게 전환
- **검색/필터**: 키워드 및 조건 기반 일정 조회
- **다크모드**: UI 테마 전환 지원
- **CSV/PNG Export**: 일정 데이터/화면 내보내기
- **오류 항목 표시**: 잘못된 형식 또는 누락된 데이터 항목 강조 표시

## 인코딩 주의사항
Windows 환경에서 한글 및 이모지(emoji) 처리를 위해 UTF-8 설정을 권장합니다.

- 터미널/에디터 인코딩을 UTF-8로 설정
- 소스 파일 저장 인코딩을 UTF-8로 유지
- 콘솔 출력 깨짐이 발생하면 PowerShell/터미널 코드 페이지를 UTF-8로 변경
  ```powershell
  chcp 65001
  ```
