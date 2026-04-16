/**
 * LandingHeader.jsx
 * 역할: 랜딩 페이지 상단 네비게이션 바
 *       - 히어로 위에 투명 오버레이로 시작 → 스크롤 시 흰색 배경으로 전환 (C 전략)
 *       - 로고 / 메뉴 링크 / "도입 문의하기" CTA 버튼
 *       - 모바일에서는 메뉴 숨김 (md 이상에서 노출)
 */

import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { handleAnchorClick, smoothScrollTo } from '../../utils/smoothScroll.js';
import ContactModal from './ContactModal.jsx';

// 네이비 원본(스크롤 후 흰 헤더용) + 흰색(최상단 어두운 히어로용)
import logoDark from '../../assets/logo/logo_transparent-removebg-preview.png';
import logoWhite from '../../assets/logo/logo_white.png';

// 네비 메뉴 항목
const NAV_LINKS = [
  { label: '서비스 소개', href: '#intro' },
  { label: '핵심 기술', href: '#features' },
  { label: '도입 사례', href: '#cases' },
];

// 스크롤 전환 기준 (px): 이 값을 넘으면 배경이 흰색으로 바뀜
const SCROLL_THRESHOLD = 50;

export default function LandingHeader() {
  // 최상단 여부: true면 투명 오버레이, false면 흰색 배경
  const [isAtTop, setIsAtTop] = useState(true);
  // 도입 문의 모달 open 여부
  const [isContactOpen, setIsContactOpen] = useState(false);
  const location = useLocation();

  // 로고 클릭: 이미 "/" 경로면 Link가 리렌더를 발생시키지 않아 스크롤이 안 먹음.
  // 현재 경로가 "/"일 때만 기본 동작을 가로채 최상단까지 스무스 스크롤.
  const handleLogoClick = (event) => {
    if (location.pathname === '/') {
      event.preventDefault();
      smoothScrollTo(0, 1000);
      if (window.history?.replaceState) {
        window.history.replaceState(null, '', '/');
      }
    }
  };

  useEffect(() => {
    // 초기 렌더 시 현재 스크롤 위치 반영 (새로고침 후 중간이면 바로 흰 배경)
    const syncScrollState = () => {
      setIsAtTop(window.scrollY < SCROLL_THRESHOLD);
    };
    syncScrollState();

    // passive: true → 스크롤 성능 향상 (기본 동작 막지 않음 명시)
    window.addEventListener('scroll', syncScrollState, { passive: true });
    return () => window.removeEventListener('scroll', syncScrollState);
  }, []);

  // //* [Modified Code] C 전략: 상단에서 투명, 스크롤 시 흰 배경 + 그림자
  const headerBgClass = isAtTop ? 'bg-transparent' : 'bg-white shadow-md';

  // 네비 링크 텍스트 색: 최상단(어두운 히어로 위)에서는 흰색, 스크롤 후엔 회색
  const navTextClass = isAtTop
    ? 'text-white/90 hover:text-white'
    : 'text-gray-600 hover:text-blue-600';

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 md:px-8 py-2 transition-colors duration-300 ${headerBgClass}`}
    >
      {/* 로고 */}
      <Link
        to="/"
        onClick={handleLogoClick}
        aria-label="DRONE INSPECT 홈"
        className="flex items-center focus:outline-none focus:ring-2 focus:ring-blue-400 rounded"
      >
        {/* //* [Modified Code] 상태에 따라 흰/네이비 로고 스왑 */}
        <img
          src={isAtTop ? logoWhite : logoDark}
          alt="DRONE INSPECT"
          className="h-16 md:h-[5rem] w-auto object-contain transition-opacity duration-300"
        />
      </Link>

      {/* 주 메뉴 */}
      <nav
        aria-label="주 메뉴"
        className="hidden md:flex space-x-10 font-semibold text-base lg:text-lg"
      >
        {NAV_LINKS.map((link) => (
          <a
            key={link.href}
            href={link.href}
            onClick={(e) => handleAnchorClick(e, link.href, 96, 1400)}
            className={`${navTextClass} transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 rounded`}
          >
            {link.label}
          </a>
        ))}
      </nav>

      {/* 우측 버튼 그룹 */}
      <div className="flex items-center gap-3">
        {/* 로그인 버튼 */}
        <Link
          to="/login"
          className={`hidden md:inline-block px-4 py-2 rounded-md font-semibold text-sm transition focus:outline-none focus:ring-2 focus:ring-blue-400 ${
            isAtTop
              ? 'text-white/90 hover:text-white hover:bg-white/10'
              : 'text-gray-600 hover:text-blue-600 hover:bg-gray-100'
          }`}
        >
          로그인
        </Link>

        {/* CTA: 최상단에서는 살짝 투명 처리, 스크롤 후엔 솔리드 */}
        <button
          type="button"
          onClick={() => setIsContactOpen(true)}
          className={`px-5 py-2.5 rounded-md font-semibold transition shadow-md focus:outline-none focus:ring-2 focus:ring-blue-400 ${
            isAtTop
              ? 'bg-blue-600/90 hover:bg-blue-600 text-white backdrop-blur-sm'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          도입 문의하기
        </button>
      </div>

      <ContactModal
        isOpen={isContactOpen}
        onClose={() => setIsContactOpen(false)}
      />
    </header>
  );
}
