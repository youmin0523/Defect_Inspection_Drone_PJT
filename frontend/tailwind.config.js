/**
 * tailwind.config.js
 * 역할: Tailwind CSS 설정
 *       - content 경로 설정 (purge 대상)
 *       - AeroInspect 브랜드 컬러 확장
 *       - 심각도별 커스텀 컬러 (HIGH:red, MED:amber, LOW:gray)
 */

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // DRONE INSPECT 브랜드 컬러 (기존 blue 계열은 보조용으로 유지)
        brand: {
          50:  '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          900: '#1e3a8a',
        },
        // //* [Modified Code] 대시보드 주 강조색 = emerald 계열 (레퍼런스 톤)
        accent: {
          50:  '#ecfdf5',
          400: '#34d399',
          500: '#10b981',
          600: '#059669',
          700: '#047857',
        },
        // 심각도별 컬러
        severity: {
          high: '#ef4444',     // red-500
          med:  '#f97316',     // orange-500
          low:  '#eab308',     // yellow-500
        },
        // //* [Modified Code] 다크 대시보드 배경 — 레퍼런스 톤 (더 진한 네이비 + 중간톤 surface)
        dashboard: {
          bg:      '#0b1120',  // 레퍼런스 메인 배경
          surface: '#111827',  // 레퍼런스 헤더/사이드 surface
          panel:   '#1f2937',  // 카드 내부 패널
          border:  '#334155',  // slate-700
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-fast': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}
