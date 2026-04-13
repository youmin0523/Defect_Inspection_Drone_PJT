# 🤖 바이브코딩(Vibe Coding) 프롬프트 & 결과 추적 로그

> **💡 설명**: 이 템플릿은 Notion에 복사하여 붙여넣기 좋게 구성되었습니다. Notion의 "데이터베이스(표)" 형태나 "하위 페이지" 형태로 사용하여 누가, 어떤 질문(프롬프트)을 통해 어떤 코드 변화를 이끌어냈는지 기록하세요.

---

## 📝 기본 정보 (Meta)

- **작성자 (Who)**: [@이름 혹은 GitHub ID]
- **작성 일자 (When)**: 202X-XX-XX
- **목표 기능 (Objective)**: (예: 프론트엔드 로그인 UI 컴포넌트에 흔들림 애니메이션 추가)
- **작업 브랜치/환경**: `feature/login-ui`

---

## 💬 바이브코딩 대화 흐름 (Vibe Coding Log)

### 1️⃣ 초기 질문 / 프롬프트 (Initial Prompt)
> *AI에게 처음 던진 질문이나 지시사항을 기록합니다.*
- **프롬프트 내용**:
  ```text
  "현재 로그인 UI 컴포넌트의 코드는 다음과 같아. [코드...].
  사용자가 비밀번호를 틀렸을 때 빨간색으로 변하면서 좌우로 흔들리는 애니메이션을 TailwindCSS로 추가해줘."
  ```

### 2️⃣ AI의 첫 번째 결과 및 분석 (AI Response & Result)
- **제공된 결과**: (예: `animate-bounce`를 활용한 코드 제공)
- **적용 후 현상**: 에러 여부, 화면 시각적 요약.
  - *예시: "코드는 정상 동작하나, 상하(bounce)로 움직여서 좌우(shake) 흔들림이라는 의도와 다름."*

### 3️⃣ 수정 프롬프트 및 트러블슈팅 (Troubleshooting Ping-Pong)
> *AI와 티키타카(Ping-pong)하며 에러를 고치거나 요구사항을 구체화한 과정을 기록합니다.*
- **내 피드백 (Prompt)**: 
  > "상하로 움직이는데 이건 틀렸어. 좌우 격하게 흔들리는 커스텀 keyframes를 tailwind.config.js에 추가하는 방식으로 다시 짜줘."
- **AI 새로운 결과**:
  > `tailwind.config.js` 수정 및 `animate-shake` 커스텀 유틸리티 생성.

---

## ✅ 최종 결과 (Final Outcome)

### 🚀 적용된 핵심 코드 스니펫 (Code Snippet)
- **어디가 어떻게 바뀌었는가?** (Better Comment 규칙 적용)
```javascript
// //! [Original Code] 흔들림 없음
// className="p-4 border-gray-300"

// //* [Modified Code] 에러 시 좌우 흔들림(animate-shake) 및 빨간색 테두리 적용
className={`p-4 transition-all ${isError ? 'border-red-500 animate-shake' : 'border-gray-300'}`}
```

### 📊 Full-Stack 영향도 (Impact)
- **프론트엔드 영향**: `tailwind.config.js`에 테마 확장, `Login.jsx` 상태 추가.
- **백엔드/API 연관성**: API 응답 코드(401 Unauthorized) 연동 완료 확인.

---

## 💡 배운 점 및 멘토의 팁 (Lessons Learned)

> 나중에 내가 보거나 다른 팀원이 볼 때 도움 되는 **인사이트**를 남깁니다.

- **문제 원인**: Tailwind 기본 제공 애니메이션에는 좌우 흔들림 `shake`가 없다는 것을 알았음.
- **해결 노하우 (바이브코딩 팁)**: AI에게 막연하게 "흔들어줘"라고 하기보다, "tailwind.config.js의 extend에 keyframes를 추가해달라"고 **기술적 제약 사항**을 구체적으로 알려주면 한 번에 정확한 답이 나온다.
