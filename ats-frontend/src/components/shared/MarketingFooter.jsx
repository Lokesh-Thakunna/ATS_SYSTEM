import { Link } from 'react-router-dom';

const footerGroups = [
  {
    title: 'Product',
    links: [
      { label: 'Platform Overview', href: '#platform' },
      { label: 'Job Pipelines', href: '#pipeline' },
      { label: 'Live Openings', href: '#jobs' },
    ],
  },
  {
    title: 'Access',
    links: [
      { label: 'Register', to: '/register' },
      { label: 'Sign In', to: '/login' },
      { label: 'Dashboard', to: '/dashboard' },
    ],
  },
];

const MarketingFooter = () => (
  <footer className="border-t border-slate-200 bg-slate-950 text-slate-300">
    <div className="mx-auto grid max-w-7xl gap-10 px-4 py-14 sm:px-6 lg:grid-cols-[1.4fr_1fr_1fr] lg:px-8">
      <div className="space-y-4">
        <p className="text-sm font-semibold uppercase tracking-[0.28em] text-cyan-300">ATSSYSTEM</p>
        <h2 className="max-w-md text-3xl font-extrabold text-white" style={{ fontFamily: 'Outfit, sans-serif' }}>
          A complete recruitment website and ATS workspace for modern hiring teams.
        </h2>
        <p className="max-w-xl text-sm leading-7 text-slate-400">
          Built for recruiters, candidates, and admins who need one clean flow for job posting, resume review, applications, and matching.
        </p>
      </div>

      {footerGroups.map((group) => (
        <div key={group.title}>
          <h3 className="text-sm font-semibold uppercase tracking-[0.22em] text-white">{group.title}</h3>
          <div className="mt-4 space-y-3">
            {group.links.map((link) => (
              link.to ? (
                <Link key={link.label} to={link.to} className="block text-sm text-slate-400 transition-colors hover:text-white">
                  {link.label}
                </Link>
              ) : (
                <a key={link.label} href={link.href} className="block text-sm text-slate-400 transition-colors hover:text-white">
                  {link.label}
                </a>
              )
            ))}
          </div>
        </div>
      ))}
    </div>

    <div className="border-t border-white/10">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-5 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <p>Copyright {new Date().getFullYear()} ATSSYSTEM. All rights reserved.</p>
        <p>Recruitment software for jobs, resumes, candidates, and hiring decisions.</p>
      </div>
    </div>
  </footer>
);

export default MarketingFooter;
