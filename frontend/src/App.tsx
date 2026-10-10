import React, { useEffect, useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { LandingPage } from './pages/LandingPage';
import { TermsPage } from './pages/legal/TermsPage';
import { PrivacyPage } from './pages/legal/PrivacyPage';
import { AcceptableUsePage } from './pages/legal/AcceptableUsePage';
import { ContactPage } from './pages/legal/ContactPage';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { CreateProjectPage } from './pages/CreateProjectPage';
import { ProjectDetailPage } from './pages/ProjectDetailPage';
import { ProfilePage } from './pages/ProfilePage';
import { ErrorBoundary } from './components/ui/ErrorBoundary';

const MainApp: React.FC = () => {
  const { user, loading } = useAuth();
  const [currentPath, setCurrentPath] = useState<string>(window.location.pathname);

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname);
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigate = (path: string) => {
    if (path.includes('#')) {
      const [p, hash] = path.split('#');
      if (p && p !== window.location.pathname) {
        window.history.pushState({}, '', p);
        setCurrentPath(p);
      }
      setTimeout(() => {
        const el = document.getElementById(hash);
        el?.scrollIntoView({ behavior: 'smooth' });
      }, 50);
      return;
    }

    window.history.pushState({}, '', path);
    setCurrentPath(path);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Route matching
  const renderRoute = () => {
    if (loading) {
      return (
        <div className="min-h-[70vh] flex items-center justify-center">
          <div className="text-center space-y-3">
            <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-xs text-slate-500 font-medium">Initializing workspace...</p>
          </div>
        </div>
      );
    }

    // Public Legal Pages
    if (currentPath === '/terms') return <TermsPage />;
    if (currentPath === '/privacy') return <PrivacyPage />;
    if (currentPath === '/acceptable-use') return <AcceptableUsePage />;
    if (currentPath === '/contact') return <ContactPage />;

    // Auth Pages
    if (currentPath === '/login') {
      if (user) {
        return <DashboardPage onNavigate={navigate} />;
      }
      return <LoginPage onNavigate={navigate} />;
    }

    if (currentPath === '/register') {
      if (user) {
        return <DashboardPage onNavigate={navigate} />;
      }
      return <RegisterPage onNavigate={navigate} />;
    }

    // Authenticated Project Pages
    if (currentPath.startsWith('/projects/')) {
      if (!user) {
        return <LoginPage onNavigate={navigate} />;
      }

      const raw = currentPath.replace('/projects/', '').split('?')[0].replace(/\/$/, '');
      if (raw === 'new') {
        return <CreateProjectPage onNavigate={navigate} />;
      }

      // Parse projectId and optional sub-path tab: e.g. /projects/:id or /projects/:id/:tab
      const parts = raw.split('/');
      const projectId = parts[0];
      const initialTab = parts[1] || undefined;

      return (
        <ErrorBoundary
          fallbackTitle="Project Workspace Error"
          fallbackMessage="An unexpected error occurred while loading this project workspace."
        >
          <ProjectDetailPage projectId={projectId} initialTab={initialTab} onNavigate={navigate} />
        </ErrorBoundary>
      );
    }

    // Dashboard
    if (currentPath === '/dashboard') {
      if (!user) {
        return <LoginPage onNavigate={navigate} />;
      }
      return <DashboardPage onNavigate={navigate} />;
    }

    // Profile & Settings
    if (currentPath === '/profile') {
      if (!user) {
        return <LoginPage onNavigate={navigate} />;
      }
      return <ProfilePage onNavigate={navigate} />;
    }

    // Root / Default
    if (user && currentPath === '/') {
      return <DashboardPage onNavigate={navigate} />;
    }
    return <LandingPage onNavigate={navigate} />;
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
      <Navbar currentPath={currentPath} onNavigate={navigate} />
      <main className="flex-1">
        <ErrorBoundary
          fallbackTitle="Application Display Error"
          fallbackMessage="An unexpected error occurred while displaying this page."
        >
          {renderRoute()}
        </ErrorBoundary>
      </main>
      <Footer onNavigate={navigate} />
    </div>
  );
};

export function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}

export default App;
