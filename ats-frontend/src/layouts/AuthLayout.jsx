import { Outlet, Link } from 'react-router-dom';

const AuthLayout = () => (
  <div className="flex min-h-screen flex-col bg-gradient-to-br from-blue-50 via-white to-slate-50">
    <header className="px-4 py-4 sm:px-6">
      <Link to="/" className="inline-flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-600">
          <span className="text-sm font-bold text-white" style={{ fontFamily: 'Syne, sans-serif' }}>A</span>
        </div>
        <span className="text-lg font-bold text-gray-900 sm:text-xl" style={{ fontFamily: 'Syne, sans-serif' }}>
          ATSSYSTEM
        </span>
      </Link>
    </header>

    <div className="flex flex-1 items-start justify-center px-4 py-8 sm:items-center sm:py-12">
      <div className="w-full max-w-md">
        <Outlet />
      </div>
    </div>

    <footer className="px-4 py-4 text-center text-xs text-gray-400">
      Copyright {new Date().getFullYear()} ATSSYSTEM. All rights reserved.
    </footer>
  </div>
);

export default AuthLayout;
