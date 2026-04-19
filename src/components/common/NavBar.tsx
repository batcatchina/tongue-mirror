import React from 'react';
import clsx from 'clsx';

interface NavBarProps {
  currentPath: string;
  onNavigate: (path: string) => void;
}

export const NavBar: React.FC<NavBarProps> = ({ currentPath, onNavigate }) => {
  const navItems = [
    { path: '/', label: '辨证', icon: '🔍', shortLabel: '辨证' },
    { path: '/cases', label: '病例', icon: '📋', shortLabel: '病例' },
    { path: '/knowledge', label: '知识库', icon: '📚', shortLabel: '知识' },
  ];

  return (
    <nav className="bg-white border-b border-stone-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14 sm:h-16">
          {/* Logo */}
          <div 
            className="flex items-center gap-2 sm:gap-3 cursor-pointer"
            onClick={() => onNavigate('/')}
          >
            <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg sm:rounded-xl bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center shadow-sm sm:shadow-md">
              <span className="text-white text-lg sm:text-xl">舌</span>
            </div>
            <div>
              <h1 className="font-chinese text-base sm:text-lg font-semibold text-stone-800">舌镜</h1>
              <p className="text-xs text-stone-400 hidden sm:block">智能辨证 · 精准选穴</p>
            </div>
          </div>

          {/* 导航链接 */}
          <div className="flex items-center gap-0.5 sm:gap-1">
            {navItems.map((item) => (
              <button
                key={item.path}
                onClick={() => onNavigate(item.path)}
                className={clsx(
                  'nav-link flex items-center gap-1 sm:gap-2 px-2 sm:px-3',
                  currentPath === item.path && 'nav-link-active'
                )}
              >
                <span className="text-sm sm:text-base">{item.icon}</span>
                <span className="text-sm hidden sm:inline">{item.label}</span>
                <span className="text-sm sm:hidden">{item.shortLabel}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default NavBar;
