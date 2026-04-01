import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ChevronDown, LogOut, User, Menu, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const Navbar = ({ onMenuToggle, menuOpen }) => {
  const { user, logout } = useAuth();
  const [dropOpen, setDropOpen] = useState(false);
  const dropRef = useRef(null);

  useEffect(() => {
    const handler = (event) => {
      if (dropRef.current && !dropRef.current.contains(event.target)) {
        setDropOpen(false);
      }
    };

    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const roleLabel = {
    admin: { text: 'ADMIN', cls: 'bg-purple-100 text-purple-700' },
    recruiter: { text: 'RECRUITER', cls: 'bg-blue-100 text-blue-700' },
    candidate: { text: 'USER', cls: 'bg-emerald-100 text-emerald-700' },
  }[user?.role] || { text: user?.role, cls: 'bg-slate-100 text-slate-600' };

  const initials = user
    ? `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase() || user.email?.[0]?.toUpperCase()
    : '?';

  return (
    <header className="fixed top-0 left-0 right-0 z-40 h-16 border-b border-slate-200/80 bg-white/95 px-4 backdrop-blur">
      <div className="mx-auto flex h-full max-w-[1600px] items-center justify-between gap-4 pl-12 lg:pl-0">
        <button
          onClick={onMenuToggle}
          className="absolute left-4 top-1/2 -translate-y-1/2 rounded-xl p-2 text-slate-500 transition-colors hover:bg-slate-100 lg:hidden"
          aria-label="Toggle menu"
        >
          {menuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>

        <Link to="/dashboard" className="flex items-center gap-2">
          <span className="text-xl font-extrabold tracking-tight text-slate-900" style={{ fontFamily: 'Syne, sans-serif' }}>
            ATS<span className="text-indigo-600">SYSTEM</span>
          </span>
        </Link>

        <div className="relative flex items-center gap-3" ref={dropRef}>
          <button
            onClick={() => setDropOpen((current) => !current)}
            className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-2 py-1.5 transition-colors hover:bg-slate-100"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-100 text-xs font-bold text-indigo-700">
              {initials}
            </div>
            <div className="hidden text-left sm:block">
              <p className="text-sm font-semibold leading-none text-slate-800">
                {user?.first_name || user?.email?.split('@')[0] || 'User'}
              </p>
              <span className={`mt-1 inline-flex rounded-full px-1.5 py-0.5 text-[10px] font-medium ${roleLabel.cls}`}>
                {roleLabel.text}
              </span>
            </div>
            <ChevronDown size={14} className="hidden text-slate-400 sm:block" />
          </button>

          <button
            type="button"
            onClick={logout}
            className="hidden rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-500 transition-colors hover:bg-slate-50 sm:inline-flex"
          >
            Sign out
          </button>

          {dropOpen && (
            <div className="absolute right-0 top-full z-50 mt-2 w-56 overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-2xl">
              <div className="border-b border-slate-100 px-4 py-3">
                <p className="text-xs text-slate-500">Signed in as</p>
                <p className="truncate text-sm font-semibold text-slate-800">{user?.email}</p>
              </div>
              <div className="p-1.5">
                <Link
                  to="/dashboard?editProfile=1"
                  onClick={() => setDropOpen(false)}
                  className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-50"
                >
                  <User size={15} className="text-slate-400" />
                  My Profile
                </Link>
                <button
                  onClick={() => { setDropOpen(false); logout(); }}
                  className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-red-600 transition-colors hover:bg-red-50"
                >
                  <LogOut size={15} />
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
