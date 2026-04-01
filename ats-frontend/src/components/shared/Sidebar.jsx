import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Briefcase, FileText,
  PlusCircle, Users, ShieldCheck, ChevronRight, Pencil, LogOut,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const candidateSections = [
  {
    title: 'Navigation',
    items: [
      { to: '/dashboard', icon: LayoutDashboard, label: 'Overview' },
      { to: '/resume', icon: FileText, label: 'My Resume' },
      { to: '/applications', icon: FileText, label: 'My Applications' },
    ],
  },
  {
    title: 'Quick Actions',
    items: [
      { to: '/jobs', icon: PlusCircle, label: 'New Application' },
      { to: '/dashboard?editProfile=1', icon: Pencil, label: 'Edit Profile' },
    ],
  },
];

const recruiterNav = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/jobs', icon: Briefcase, label: 'All Jobs' },
  { to: '/recruiter/jobs', icon: PlusCircle, label: 'My Postings' },
  { to: '/recruiter/applicants', icon: Users, label: 'Applicants' },
];

const adminNav = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/jobs', icon: Briefcase, label: 'All Jobs' },
  { to: '/admin/recruiters', icon: ShieldCheck, label: 'Recruiters' },
];

const navByRole = { recruiter: recruiterNav, admin: adminNav };

const NavItem = ({ to, icon: Icon, label, onClick }) => (
  <NavLink
    to={to}
    onClick={onClick}
    className={({ isActive }) =>
      `flex items-center gap-3 px-3 py-2.5 rounded-2xl text-sm font-medium transition-all group ${
        isActive
          ? 'bg-indigo-50 text-indigo-700 shadow-sm'
          : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
      }`
    }
  >
    {({ isActive }) => (
      <>
        <Icon size={17} className={isActive ? 'text-indigo-600' : 'text-slate-400 group-hover:text-slate-600'} />
        <span className="flex-1">{label}</span>
        {isActive && <ChevronRight size={14} className="text-indigo-400" />}
      </>
    )}
  </NavLink>
);

const Sidebar = ({ open, onClose }) => {
  const { user, logout } = useAuth();
  const isCandidate = user?.role === 'candidate';
  const navItems = navByRole[user?.role] || [];

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-30 bg-slate-900/25 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed left-0 top-16 bottom-0 z-30 w-72 border-r border-slate-200/80 bg-white/95
          flex flex-col transition-transform duration-300
          ${open ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0
        `}
      >
        <div className="flex-1 overflow-y-auto px-4 py-5">
          <div className="rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-xl font-extrabold text-slate-900" style={{ fontFamily: 'Syne, sans-serif' }}>
              ATS<span className="text-indigo-600">SYSTEM</span>
            </p>
            <p className="mt-1 text-xs font-medium text-emerald-600">{isCandidate ? 'Candidate Portal' : 'Workspace'}</p>
          </div>

          {isCandidate ? (
            <div className="mt-6 space-y-6">
              {candidateSections.map((section) => (
                <div key={section.title}>
                  <p className="mb-2 px-2 text-[10px] font-bold uppercase tracking-[0.22em] text-slate-400">{section.title}</p>
                  <div className="space-y-1">
                    {section.items.map((item) => <NavItem key={item.to} {...item} onClick={onClose} />)}
                  </div>
                </div>
              ))}

              <div>
                <p className="mb-2 px-2 text-[10px] font-bold uppercase tracking-[0.22em] text-slate-400">Account</p>
                <button
                  type="button"
                  onClick={() => { onClose?.(); logout(); }}
                  className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-sm font-medium text-rose-600 transition-colors hover:bg-rose-50"
                >
                  <LogOut size={17} />
                  <span className="flex-1 text-left">Sign Out</span>
                </button>
              </div>
            </div>
          ) : (
            <nav className="mt-6 space-y-1">
              <p className="mb-2 px-2 text-[10px] font-bold uppercase tracking-[0.22em] text-slate-400">Navigation</p>
              {navItems.map((item) => (
                <NavItem key={item.to} {...item} onClick={onClose} />
              ))}
            </nav>
          )}
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
