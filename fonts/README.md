# 한글 PDF 폰트 (맑은 고딕 호환)

PDF 보고서는 **맑은 고딕에 가까운 나눔고딕 계열로 통일**해 한글이 깨지지 않도록 합니다.

- **Windows**: `C:\Windows\Fonts\malgun.ttf`(맑은 고딕) 자동 사용
- **그 외(서버/배포)**: 이 폴더의 `NanumGothic.ttf` 또는 `NanumGothic-Regular.ttf` 사용  
  - 없으면 **첫 PDF 생성 시** 나눔고딕을 자동 다운로드해 이 폴더에 저장합니다.

**배포 환경에서 한글이 깨질 때** 이 폴더에 아래 중 하나를 넣어 두세요.

- **NanumGothic-Regular.ttf** — [Google Fonts 나눔고딕](https://github.com/google/fonts/raw/refs/heads/main/ofl/nanumgothic/NanumGothic-Regular.ttf) (권장)
- **NanumGothic.ttf** — [나눔고딕](https://github.com/naver/nanumfont/raw/master/NanumGothic.ttf)
- **NotoSansKR-Regular.ttf** — [Google Noto Sans KR](https://fonts.google.com/noto/specimen/Noto+Sans+KR)
