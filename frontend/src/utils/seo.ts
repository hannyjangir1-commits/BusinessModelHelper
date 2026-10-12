/**
 * SEO & Route-Aware Metadata Manager.
 * Handles titles, meta descriptions, canonical links, and indexing policies
 * without leaking confidential authenticated project names or private user data.
 */

export interface RouteMeta {
  title: string;
  description: string;
  robots: string;
  isPublicIndexable: boolean;
}

export const ROUTE_METADATA_CONFIG: Record<string, RouteMeta> = {
  '/': {
    title: 'AI Business Architect - Strategic Business Modeling & Architecture Blueprint Engine',
    description:
      'Transform startup concepts into actionable Business Model Canvases, enterprise architecture blueprints, verified market research, and financial plans with AI.',
    robots: 'index, follow',
    isPublicIndexable: true,
  },
  '/terms': {
    title: 'Terms and Conditions - AI Business Architect',
    description: 'Terms of service, usage guidelines, and legal framework for AI Business Architect.',
    robots: 'index, follow',
    isPublicIndexable: true,
  },
  '/privacy': {
    title: 'Privacy Policy - AI Business Architect',
    description: 'Understand how AI Business Architect handles enterprise data, customer privacy, and credentials.',
    robots: 'index, follow',
    isPublicIndexable: true,
  },
  '/acceptable-use': {
    title: 'Acceptable Use Policy - AI Business Architect',
    description: 'Ethical generation standards and acceptable use policies for AI Business Architect.',
    robots: 'index, follow',
    isPublicIndexable: true,
  },
  '/contact': {
    title: 'Contact Support - AI Business Architect',
    description: 'Get in touch with the AI Business Architect development and product team.',
    robots: 'index, follow',
    isPublicIndexable: true,
  },
  '/login': {
    title: 'Sign In - AI Business Architect',
    description: 'Sign in to access your business venture blueprints and architecture workspaces.',
    robots: 'noindex, follow',
    isPublicIndexable: false,
  },
  '/register': {
    title: 'Create an Account - AI Business Architect',
    description: 'Register for AI Business Architect to begin generating strategic business blueprints.',
    robots: 'noindex, follow',
    isPublicIndexable: false,
  },
  '/dashboard': {
    title: 'Dashboard - AI Business Architect',
    description: 'Manage your portfolio of business ventures and architectural blueprints.',
    robots: 'noindex, nofollow',
    isPublicIndexable: false,
  },
  '/profile': {
    title: 'Profile & Settings - AI Business Architect',
    description: 'Manage personal credentials, preferences, and account security.',
    robots: 'noindex, nofollow',
    isPublicIndexable: false,
  },
};

/**
 * Resolve metadata for a given pathname.
 * Authenticated project workspaces strictly use generic metadata to prevent
 * publishing private or confidential client project information in document titles.
 */
export function getRouteMetadata(pathname: string): RouteMeta {
  const normalized = pathname.split('?')[0].split('#')[0].replace(/\/$/, '') || '/';

  if (ROUTE_METADATA_CONFIG[normalized]) {
    return ROUTE_METADATA_CONFIG[normalized];
  }

  if (normalized.startsWith('/projects/')) {
    return {
      title: 'Project Workspace - AI Business Architect',
      description: 'Strategic planning, architecture blueprints, and validation workspace.',
      robots: 'noindex, nofollow',
      isPublicIndexable: false,
    };
  }

  // Fallback for 404 / unrecognized routes
  return {
    title: 'Page Not Found (404) - AI Business Architect',
    description: 'The requested page could not be found.',
    robots: 'noindex, follow',
    isPublicIndexable: false,
  };
}

/**
 * Resolves the configured canonical origin without inventing unverified domains.
 * Reads VITE_PUBLIC_SITE_URL or returns null if unconfigured.
 */
export function getPublicSiteUrl(): string | null {
  const envUrl =
    typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_PUBLIC_SITE_URL
      ? String(import.meta.env.VITE_PUBLIC_SITE_URL).trim()
      : null;

  if (envUrl && envUrl.startsWith('http')) {
    return envUrl.replace(/\/$/, '');
  }
  return null;
}

/**
 * Updates head metadata dynamically based on current route.
 */
export function updateRouteMetadata(pathname: string): void {
  if (typeof document === 'undefined') return;

  const meta = getRouteMetadata(pathname);
  document.title = meta.title;

  // Update or create meta description
  let descTag = document.querySelector<HTMLMetaElement>('meta[name="description"]');
  if (!descTag) {
    descTag = document.createElement('meta');
    descTag.name = 'description';
    document.head.appendChild(descTag);
  }
  descTag.content = meta.description;

  // Update or create meta robots
  let robotsTag = document.querySelector<HTMLMetaElement>('meta[name="robots"]');
  if (!robotsTag) {
    robotsTag = document.createElement('meta');
    robotsTag.name = 'robots';
    document.head.appendChild(robotsTag);
  }
  robotsTag.content = meta.robots;

  // Canonical link: only add if public site URL is configured and route is indexable
  const siteUrl = getPublicSiteUrl();
  let canonicalTag = document.querySelector<HTMLLinkElement>('link[rel="canonical"]');

  if (siteUrl && meta.isPublicIndexable) {
    const cleanPath = pathname === '/' ? '' : pathname.replace(/\/$/, '');
    const canonicalUrl = `${siteUrl}${cleanPath}`;

    if (!canonicalTag) {
      canonicalTag = document.createElement('link');
      canonicalTag.rel = 'canonical';
      document.head.appendChild(canonicalTag);
    }
    canonicalTag.href = canonicalUrl;
  } else if (canonicalTag) {
    // Remove canonical tag if unconfigured or private route to prevent duplicate/invalid canonicals
    canonicalTag.remove();
  }
}
