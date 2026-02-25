# OPENAI_API_KEY 설정 (간단·안정)

하나만 쓰면 됩니다. **배포 환경에서는 ①, 로컬에서는 ②**가 가장 안정적입니다.

---

## ① 배포 후 (Render, Apache, 호스팅 등) — 권장

**호스트에서 환경 변수로만 설정**하면 됩니다. `.env` 파일은 필요 없습니다.

- **Render**: Dashboard → Service → Environment → Key `OPENAI_API_KEY`, Value `sk-proj-...` 추가
- **Apache**: VirtualHost 또는 `.htaccess`에 `SetEnv OPENAI_API_KEY "sk-proj-..."`
- **기타**: 해당 서비스 문서에서 "Environment Variables" 설정 방법대로 `OPENAI_API_KEY` 추가

→ PHP/Python 모두 `getenv('OPENAI_API_KEY')`로 읽으므로, 한 번만 설정하면 됩니다.

---

## ② 로컬 테스트 (가장 간단)

1. 프로젝트 루트에 **`.env`** 파일이 없다면 생성합니다.
2. 다음 한 줄을 넣고 저장합니다 (실제 키로 바꿉니다).

   ```env
   OPENAI_API_KEY=sk-proj-여기에_실제_키
   ```

3. PHP 스크립트는 실행 시 **`load_env.php`**가 `.env`를 읽어 환경 변수로 넣습니다. 별도 설정 없이 동작합니다.
4. **`.env`는 Git에 올리지 않습니다.** (이미 `.gitignore`에 있음)

---

## 동작 방식 요약

| 구분       | 설정 방법                    | 비고 |
|------------|-----------------------------|------|
| **배포**   | 호스트의 Environment Variables에 `OPENAI_API_KEY` 설정 | 서버 값이 우선, 안정적 |
| **로컬**   | 프로젝트 루트 `.env`에 `OPENAI_API_KEY=sk-...` 한 줄 | `load_env.php`가 자동 로드 |

이미 서버에 `OPENAI_API_KEY`가 설정되어 있으면 `.env`는 무시되므로, **배포 후 안정성**을 유지할 수 있습니다.
