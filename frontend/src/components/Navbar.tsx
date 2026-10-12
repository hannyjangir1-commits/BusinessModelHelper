import React, { useEffect, useRef, useState } from 'react';
import { Layers, LogOut, Menu, Plus, User as UserIcon, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/Button';

interface NavbarProps {
  currentPath: string;
  onNavigate: (path: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentPath, onNavigate }) => {
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  const handleNav = (path: string) => {
    onNavigate(path);
    setMobileMenuOpen(false);
    setUserDropdownOpen(false);
  };

  const handleLogout = async () => {
    await logout();
    handleNav('/');
  };

  // Keyboard accessibility & click outside handlers for disclosures
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setUserDropdownOpen(false);
        setMobileMenuOpen(false);
      }
    };

    const handleClickOutside = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserDropdownOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand: Semantic accessible button instead of clickable div */}
          <button
            type="button"
            onClick={() => handleNav(user ? '/dashboard' : '/')}
            className="flex items-center gap-2.5 text-left cursor-pointer select-none focus:outline-hidden focus:ring-2 focus:ring-indigo-500 rounded-xl p-1"
            aria-label="AI Business Architect Home"
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-700 via-indigo-600 to-indigo-500 flex items-center justify-center text-white shadow-xs">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <span className="font-extrabold text-base tracking-tight text-slate-900 block leading-tight">
                AI Business Architect
              </span>
              <span className="text-[10px] text-indigo-600 font-semibold tracking-wider uppercase block">
                Enterprise Blueprint
              </span>
            </div>
          </button>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-6" aria-label="Main Navigation">
            {!user ? (
              <>
                <button
                  onClick={() => handleNav('/')}
                  className={`text-sm font-medium transition-colors ${
                    currentPath === '/' ? 'text-indigo-600' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Overview
                </button>
                <button
                  onClick={() => handleNav('/#features')}
                  className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
                >
                  Features
                </button>
                <button
                  onClick={() => handleNav('/#how-it-works')}
                  className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
                >
                  How it Works
                </button>
                <button
                  onClick={() => handleNav('/#faq')}
                  className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
                >
                  FAQ
                </button>
                <div className="h-4 w-px bg-slate-200" />
                <Button variant="ghost" size="sm" onClick={() => handleNav('/login')}>
                  Sign In
                </Button>
                <Button variant="primary" size="sm" onClick={() => handleNav('/register')}>
                  Start Building
                </Button>
              </>
            ) : (
              <>
                <button
                  onClick={() => handleNav('/dashboard')}
                  className={`text-sm font-medium transition-colors ${
                    currentPath === '/dashboard'
                      ? 'text-indigo-600 font-semibold'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Dashboard
                </button>
                <button
                  onClick={() => handleNav('/projects/new')}
                  className={`text-sm font-medium transition-colors flex items-center gap-1.5 ${
                    currentPath === '/projects/new'
                      ? 'text-indigo-600 font-semibold'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <Plus className="w-4 h-4" />
                  New Project
                </button>

                {/* User Menu Disclosure */}
                <div className="relative" ref={userMenuRef}>
                  <button
                    id="user-menu-button"
                    type="button"
                    onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                    aria-haspopup="true"
                    aria-expanded={userDropdownOpen}
                    aria-controls="user-dropdown-menu"
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 transition-colors text-sm font-medium text-slate-700"
                  >
                    <div className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xs">
                      {user.display_name?.charAt(0).toUpperCase() || user.username.charAt(0).toUpperCase()}
                    </div>
                    <span>{user.display_name || user.username}</span>
                  </button>

                  {userDropdownOpen && (
                    <div
                      id="user-dropdown-menu"
                      role="menu"
                      aria-labelledby="user-menu-button"
                      className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border border-slate-200 py-1.5 z-50 animate-in fade-in zoom-in-95 duration-100"
                    >
                      <div className="px-4 py-2 border-b border-slate-100">
                        <p className="text-xs text-slate-500">Signed in as</p>
                        <p className="text-xs font-semibold text-slate-800 truncate">{user.email}</p>
                      </div>
                      <button
                        role="menuitem"
                        onClick={() => handleNav('/profile')}
                        className="w-full text-left px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 flex items-center gap-2 focus:outline-hidden focus:bg-slate-100"
                      >
                        <UserIcon className="w-3.5 h-3.5 text-slate-500" />
                        Profile & Settings
                      </button>
                      <button
                        role="menuitem"
                        onClick={handleLogout}
                        className="w-full text-left px-4 py-2 text-xs font-medium text-rose-600 hover:bg-rose-50 flex items-center gap-2 focus:outline-hidden focus:bg-rose-50"
                      >
                        <LogOut className="w-3.5 h-3.5 text-rose-500" />
                        Sign Out
                      </button>
                    </div>
                  )}
                </div>
              </>
            )}
          </nav>

          {/* Mobile Menu Toggle Button */}
          <div className="flex md:hidden items-center">
            <button
              id="mobile-menu-button"
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-navigation-menu"
              className="p-2.5 min-w-[44px] min-h-[44px] flex items-center justify-center text-slate-600 hover:text-slate-900 rounded-lg hover:bg-slate-100 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
              aria-label={mobileMenuOpen ? 'Close Navigation Menu' : 'Open Navigation Menu'}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer Disclosure */}
      {mobileMenuOpen && (
        <div
          id="mobile-navigation-menu"
          aria-labelledby="mobile-menu-button"
          className="md:hidden border-t border-slate-200 bg-white px-4 pt-3 pb-6 space-y-3"
        >
          {!user ? (
            <>
              <button
                onClick={() => handleNav('/')}
                className="block w-full text-left py-2.5 text-sm font-medium text-slate-700 hover:text-slate-900"
              >
                Home
              </button>
              <button
                onClick={() => handleNav('/terms')}
                className="block w-full text-left py-2.5 text-sm font-medium text-slate-700 hover:text-slate-900"
              >
                Terms and Conditions
              </button>
              <button
                onClick={() => handleNav('/privacy')}
                className="block w-full text-left py-2.5 text-sm font-medium text-slate-700 hover:text-slate-900"
              >
                Privacy Policy
              </button>
              <div className="pt-2 flex flex-col gap-2">
                <Button variant="outline" className="w-full justify-center min-h-[44px]" onClick={() => handleNav('/login')}>
                  Sign In
                </Button>
                <Button variant="primary" className="w-full justify-center min-h-[44px]" onClick={() => handleNav('/register')}>
                  Start Building Free
                </Button>
              </div>
            </>
          ) : (
            <>
              <div className="px-2 py-1.5 bg-slate-50 rounded-lg mb-2">
                <p className="text-xs text-slate-500">Logged in as</p>
                <p className="text-sm font-semibold text-slate-800">{user.display_name || user.username}</p>
              </div>
              <button
                onClick={() => handleNav('/dashboard')}
                className="block w-full text-left py-2.5 text-sm font-medium text-slate-700 hover:text-slate-900"
              >
                Dashboard
              </button>
              <button
                onClick={() => handleNav('/projects/new')}
                className="block w-full text-left py-2.5 text-sm font-medium text-slate-700 hover:text-slate-900"
              >
                Create New Project
              </button>
              <button
                onClick={() => handleNav('/profile')}
                className="block w-full text-left py-2.5 text-sm font-medium text-slate-700 hover:text-slate-900"
              >
                Profile & Settings
              </button>
              <div className="pt-2">
                <Button variant="destructive" size="sm" className="w-full justify-center min-h-[44px]" onClick={handleLogout}>
                  Sign Out
                </Button>
              </div>
            </>
          )}
        </div>
      )}
    </header>
  );
};
