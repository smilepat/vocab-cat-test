# Vercel 프론트엔드 배포 가이드

## 방법 1: GitHub 연동 (권장)

### 1. GitHub 저장소 준비
```bash
# 현재 저장소가 GitHub에 있는지 확인
git remote -v

# 없다면 GitHub에 저장소 생성 후
git remote add origin https://github.com/YOUR_USERNAME/vocab-cat-test.git
git push -u origin main
```

### 2. Vercel 대시보드에서 배포

1. https://vercel.com 접속 및 로그인
2. "Add New..." → "Project" 클릭
3. GitHub 저장소 import
4. 프로젝트 설정:
   - **Framework Preset**: Vite
   - **Root Directory**: `irt_cat_engine/frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

5. 환경 변수 추가:
   ```
   Name: VITE_API_BASE
   Value: https://your-cloud-run-url.run.app/api/v1
   ```

6. "Deploy" 클릭

### 3. 자동 배포 설정

이후 main 브랜치에 push하면 자동으로 재배포됩니다:
```bash
git add .
git commit -m "Update frontend"
git push origin main
```

---

## 방법 2: Vercel CLI 사용

### 1. Vercel CLI 설치
```bash
npm install -g vercel
```

### 2. 로그인
```bash
vercel login
```

### 3. 프로젝트 배포

#### 초기 배포
```bash
cd irt_cat_engine/frontend

# Development 배포 (테스트용)
vercel

# Production 배포
vercel --prod
```

배포 중 질문에 답변:
- Set up and deploy?: `Y`
- Which scope?: 선택
- Link to existing project?: `N` (처음) / `Y` (재배포)
- Project name?: `vocab-cat-frontend`
- Directory: `./` (이미 frontend 디렉토리 안)
- Override settings?: `N`

### 4. 환경 변수 설정

```bash
# Production 환경 변수 추가
vercel env add VITE_API_BASE production
# 값 입력: https://your-cloud-run-url.run.app/api/v1

# Preview 환경 변수 (선택사항)
vercel env add VITE_API_BASE preview
# 값 입력: https://your-staging-url.run.app/api/v1

# Development 환경 변수 (선택사항)
vercel env add VITE_API_BASE development
# 값 입력: http://localhost:8000/api/v1
```

### 5. 환경 변수 확인
```bash
vercel env ls
```

### 6. 재배포 (환경 변수 변경 후)
```bash
vercel --prod
```

---

## vercel.json 설정 (선택사항)

프로젝트 루트에 `vercel.json` 생성:

```json
{
  "buildCommand": "cd irt_cat_engine/frontend && npm run build",
  "outputDirectory": "irt_cat_engine/frontend/dist",
  "framework": "vite",
  "env": {
    "VITE_API_BASE": "@vite_api_base"
  }
}
```

---

## 커스텀 도메인 설정

### Vercel 대시보드에서:
1. 프로젝트 → Settings → Domains
2. 도메인 추가 (예: vocab-cat.yourdomain.com)
3. DNS 설정:
   - Type: CNAME
   - Name: vocab-cat
   - Value: cname.vercel-dns.com

---

## 배포 확인

### 1. 배포 URL 확인
```bash
vercel ls
```

### 2. 배포 상태 확인
```bash
# 최근 배포 로그
vercel logs

# 특정 배포 로그
vercel logs DEPLOYMENT_URL
```

### 3. 브라우저에서 확인
- 프로덕션: `https://vocab-cat-frontend.vercel.app`
- API 연결 테스트: 테스트 시작 버튼 클릭

---

## 빌드 최적화

### vite.config.ts 업데이트

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: false, // Production에서 소스맵 비활성화
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['react', 'react-dom'],
        },
      },
    },
  },
  define: {
    'import.meta.env.VITE_API_BASE': JSON.stringify(
      process.env.VITE_API_BASE || 'http://localhost:8000/api/v1'
    ),
  },
})
```

---

## Preview 배포 (PR 테스트)

Pull Request 생성 시 자동으로 Preview 배포:
```bash
git checkout -b feature/new-feature
git add .
git commit -m "Add new feature"
git push origin feature/new-feature
# GitHub에서 PR 생성 → Vercel이 자동으로 Preview 배포
```

---

## 환경별 설정

### Production
```env
VITE_API_BASE=https://vocab-cat-api-xxxxx.run.app/api/v1
```

### Staging
```env
VITE_API_BASE=https://vocab-cat-api-staging-xxxxx.run.app/api/v1
```

### Development
```env
VITE_API_BASE=http://localhost:8000/api/v1
```

---

## 트러블슈팅

### 빌드 실패
```bash
# 로컬에서 빌드 테스트
cd irt_cat_engine/frontend
npm run build

# 문제 해결 후 재배포
vercel --prod
```

### 환경 변수가 적용 안 됨
```bash
# 환경 변수 확인
vercel env ls

# 캐시 클리어 후 재배포
vercel --prod --force
```

### CORS 에러
백엔드의 ALLOWED_ORIGINS에 Vercel URL 추가:
```bash
gcloud run services update vocab-cat-api \
  --update-env-vars ALLOWED_ORIGINS="https://vocab-cat-frontend.vercel.app,https://vocab-cat.yourdomain.com" \
  --region us-central1
```

---

## 성능 최적화

### 1. Vercel Analytics 활성화
```bash
npm install @vercel/analytics
```

```typescript
// main.tsx
import { Analytics } from '@vercel/analytics/react';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
      <Analytics />
    </ErrorBoundary>
  </StrictMode>,
)
```

### 2. Edge Functions (선택사항)
API 프록시를 위한 Edge Function 설정

---

## 배포 완료 체크리스트

- [ ] 프로덕션 배포 완료
- [ ] 환경 변수 설정 (VITE_API_BASE)
- [ ] 백엔드 CORS 설정에 프론트엔드 URL 추가
- [ ] 커스텀 도메인 설정 (선택사항)
- [ ] API 연결 테스트
- [ ] 전체 사용자 플로우 테스트
- [ ] Analytics 설정 (선택사항)

---

**배포된 URL**: https://vocab-cat-frontend.vercel.app

**다음 단계**: 백엔드 CORS에 이 URL을 추가하세요!
