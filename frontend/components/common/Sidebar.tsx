'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutGrid, Briefcase, Users, Search, BarChart3, Settings, LogOut } from 'lucide-react';
import { useAuth } from '@/lib/auth';

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutGrid },
  { href: '/jobs', label: 'Jobs', icon: Briefcase },
  { href: '/candidates', label: 'Candidates', icon: Users },
  { href: '/search', label: 'Search', icon: Search },
  { href: '/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="flex h-screen w-60 flex-col border-r border-line bg-paperRaised">
      <div className="flex items-center gap-2 px-5 py-5">
        <LensMark />
        <span className="font-display text-[17px] font-semibold tracking-tight">TalentLens</span>
      </div>

      <nav className="flex-1 space-y-0.5 px-3">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + '/');
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-2.5 rounded px-3 py-2 text-sm transition-colors ${
                active ? 'bg-lens-faint text-lens font-medium' : 'text-ink-soft hover:bg-paper'
              }`}
            >
              <Icon size={17} strokeWidth={2} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-line px-3 py-3">
        <div className="flex items-center justify-between rounded px-2 py-2">
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{user?.name}</p>
            <p className="truncate text-xs text-ink-faint">{user?.role}</p>
          </div>
          <button
            onClick={logout}
            aria-label="Log out"
            className="rounded p-1.5 text-ink-faint hover:bg-paper hover:text-ink"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  );
}

function LensMark() {
  // Small aperture-blade mark echoing ScoreRing, used as the wordmark icon.
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
      {Array.from({ length: 8 }, (_, i) => {
        const angle = (i / 8) * 360 - 90;
        const rad = (angle * Math.PI) / 180;
        const x1 = 11 + Math.cos(rad) * 4;
        const y1 = 11 + Math.sin(rad) * 4;
        const x2 = 11 + Math.cos(rad) * 9.5;
        const y2 = 11 + Math.sin(rad) * 9.5;
        return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#3B2FA3" strokeWidth="2.2" strokeLinecap="round" />;
      })}
    </svg>
  );
}
