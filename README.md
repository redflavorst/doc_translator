# Doc Translator

로컬 환경에서 문서 번역을 수행하는 도구입니다. Flask, pywebview, Ollama를 사용하여 구현되었습니다.

## 주요 기능

- PDF, 워드 문서 등의 텍스트 추출
- 마크다운 형식으로 변환
- 헤더 기반 문서 분할을 통한 효율적인 번역
- 실시간 번역 진행 상황 모니터링

## 시스템 요구사항

- Python 3.8 이상
- Windows, macOS, Linux (Windows에서 테스트 완료)

## 설치 방법

1. 저장소 클론:
   ```bash
   git clone [저장소 URL]
   cd doc_translator
   ```

2. 가상환경 생성 및 활성화 (권장):
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. 의존성 설치:
   ```bash
   pip install -r requirements.txt
   ```

## 실행 방법

1. 간편 실행 (Windows):
   - `run.bat` 파일을 더블클릭하거나 명령 프롬프트에서 실행

2. 수동 실행:
   ```bash
   python app.py
   ```

## 의존성 설치 참고사항

### 1. Poppler 설치 (PDF 처리용)
- Windows: [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases/)에서 다운로드 후 시스템 PATH에 추가
- macOS: `brew install poppler`
- Linux (Ubuntu/Debian): `sudo apt-get install poppler-utils`

### 2. Tesseract OCR (선택사항, 이미지 기반 PDF용)
- Windows: [Tesseract 설치 가이드](https://github.com/UB-Mannheim/tesseract/wiki)
- macOS: `brew install tesseract`
- Linux (Ubuntu/Debian): `sudo apt-get install tesseract-ocr`

## 문제 해결

- **가져오기 오류 발생 시**: 필요한 패키지가 모두 설치되어 있는지 확인하세요.
  ```bash
  pip install -r requirements.txt
  ```

- **PDF 변환 오류**: Poppler가 올바르게 설치되어 있고 시스템 PATH에 추가되었는지 확인하세요.

- **OCR 관련 오류**: Tesseract OCR이 설치되어 있지 않으면 OCR 기능을 사용할 수 없습니다.

## 라이선스

MIT License
