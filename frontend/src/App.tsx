import React, { Suspense, useEffect, useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { ErrorBoundary } from './components/ui/ErrorBoundary';
import { updateRouteMetadata } from './utils/seo';

// Lazy-loaded route components for optimized bundle splitting
const LandingPage = React.lazy(() => import('./pages/LandingPage').then((m) => ({ default: m.LandingPage })));
const TermsPage = React.lazy(() => import('./pages/legal/TermsPage').then((m) => ({ default: m.TermsPage })));
const PrivacyPage = React.lazy(() => import('./pages/legal/PrivacyPage').then((m) => ({ default: m.PrivacyPage })));
const AcceptableUsePage = React.lazy(() => import('./pages/legal/AcceptableUsePage').then((m) => ({ default: m.AcceptableUsePage })));
const ContactPage = React.lazy(() => import('./pages/legal/ContactPage').then((m) => ({ default: m.ContactPage })));
const LoginPage = React.lazy(() => import('./pages/auth/LoginPage').then((m) => ({ default: m.LoginPage })));
const RegisterPage = React.lazy(() => import('./pages/auth/RegisterPage').then((m) => ({ default: m.RegisterPage })));
const DashboardPage = React.lazy(() => import('./pages/DashboardPage').then((m) => ({ default: m.DashboardPage })));
const CreateProjectPage = React.lazy(() => import('./pages/CreateProjectPage').then((m) => ({ default: m.CreateProjectPage })));
const ProjectDetailPage = React.lazy(() => import('./pages/ProjectDetailPage').then((m) => ({ default: m.ProjectDetailPage })));
const ProfilePage = React.lazy(() => import('./pages/ProfilePage').then((m) => ({ default: m.ProfilePage })));
const NotFoundPage = React.lazy(() => import('./pages/NotFoundPage').then((m) => ({ default: m.NotFoundPage })));

const RouteLoadingFallback: React.FC = () => (
  <div className="min-h-[50vh] flex items-center justify-center" role="status" aria-label="Loading page view">
    <div className="text-center space-y-3">
      <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto" />
      <p className="text-xs text-slate-500 font-medium">Loading view...</p>
    </div>
  </div>
);

const MainApp: React.FC = () => {
  const { user, loading } = useAuth();
  const [currentPath, setCurrentPath] = useState<string>(window.location.pathname);

  useEffect(() => {
    updateRouteMetadata(currentPath);
  }, [currentPath]);

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

    // Root Route
    if (currentPath === '/') {
      if (user) {
        return <DashboardPage onNavigate={navigate} />;
      }
      return <LandingPage onNavigate={navigate} />;
    }

    // Unrecognized route -> Helpful 404 Not Found Page
    return <NotFoundPage onNavigate={navigate} />;
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
      {/* Accessible Skip Navigation Link */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2.5 focus:bg-indigo-600 focus:text-white focus:font-semibold focus:rounded-lg focus:shadow-lg focus:outline-hidden focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
      >
        Skip to main content
      </a>

      <Navbar currentPath={currentPath} onNavigate={navigate} />
      <main id="main-content" tabIndex={-1} className="flex-1 focus:outline-hidden">
        <ErrorBoundary
          fallbackTitle="Application Display Error"
          fallbackMessage="An unexpected error occurred while displaying this page."
        >
          <Suspense fallback={<RouteLoadingFallback />}>
            {renderRoute()}
          </Suspense>
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
