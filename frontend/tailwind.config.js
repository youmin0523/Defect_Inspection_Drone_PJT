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
        // AeroInspect 브랜드 컬러
        brand: {
          50:  '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          900: '#1e3a8a',
        },
        // 심각도별 컬러
        severity: {
          high: '#ef4444',     // red-500
          med:  '#f97316',     // orange-500
          low:  '#eab308',     // yellow-500
        },
        // 다크 대시보드 배경
        dashboard: {
          bg:      '#0f172a',  // slate-900
          surface: '#1e293b',  // slate-800
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
