import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Menu, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const navLinks = [
  { label: 'Platform', href: '#platform' },
  { label: 'Modules', href: '#modules' },
  { label: 'Pipeline', href: '#pipeline' },
  { label: 'Jobs', href: '#jobs' },
];

const MarketingNavbar = () => {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);

  const primaryLink = user ? '/dashboard' : '/register';
  const primaryLabel = user ? 'Open Dashboard' : 'Start Free';
  const secondaryLink = user ? '/jobs' : '/login';
  const secondaryLabel = user ? 'Browse Jobs' : 'Sign In';

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200/70 bg-white/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#0f172a_0%,#2563eb_55%,#14b8a6_100%)] shadow-[0_12px_24px_rgba(37,99,235,0.22)]">
            <span className="text-sm font-extrabold tracking-[0.22em] text-white" style={{ fontFamily: 'Outfit, sans-serif' }}>
              ATS
            </span>
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-sky-600">Recruitment Platform</p>
            <p className="text-lg font-extrabold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
              ATSSYSTEM
            </p>
          </div>
        </Link>

        <nav className="hidden items-center gap-8 lg:flex">
          {navLinks.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="text-sm font-medium text-slate-600 transition-colors hover:text-slate-950"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-3 lg:flex">
          <Link to={secondaryLink} className="btn-secondary">
            {secondaryLabel}
          </Link>
          <Link to={primaryLink} className="btn-primary">
            {primaryLabel}
            <ArrowRight size={16} />
          </Link>
        </div>

        <button
          type="button"
          onClick={() => setOpen((current) => !current)}
          className="inline-flex rounded-2xl border border-slate-200 p-2 text-slate-600 transition-colors hover:bg-slate-50 lg:hidden"
          aria-label="Toggle navigation"
        >
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {open && (
        <div className="border-t border-slate-200 bg-white lg:hidden">
          <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:px-6">
            {navLinks.map((item) => (
              <a
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className="rounded-2xl px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-950"
              >
                {item.label}
              </a>
            ))}
            <div className="mt-2 flex flex-col gap-3">
              <Link to={secondaryLink} onClick={() => setOpen(false)} className="btn-secondary justify-center">
                {secondaryLabel}
              </Link>
              <Link to={primaryLink} onClick={() => setOpen(false)} className="btn-primary justify-center">
                {primaryLabel}
                <ArrowRight size={16} />
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};

export default MarketingNavbar;
