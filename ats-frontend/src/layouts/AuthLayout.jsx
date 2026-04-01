import { Outlet, Link } from 'react-router-dom';

const AuthLayout = () => (
  <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-slate-50 flex flex-col">
    {/* Top bar */}
    <header className="px-6 py-4">
      <Link to="/" className="inline-flex items-center gap-2">
        <div className="w-8 h-8 rounded-xl bg-blue-600 flex items-center justify-center">
          <span className="text-white font-bold text-sm" style={{ fontFamily: 'Syne, sans-serif' }}>A</span>
        </div>
        <span className="font-bold text-gray-900 text-xl" style={{ fontFamily: 'Syne, sans-serif' }}>
          ATSSYSTEM
        </span>
      </Link>
    </header>

    {/* Centered form */}
    <div className="flex-1 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <Outlet />
      </div>
    </div>

    {/* Footer */}
    <footer className="text-center py-4 text-xs text-gray-400">
      © {new Date().getFullYear()} ATSSYSTEM. All rights reserved.
    </footer>
  </div>
);

export default AuthLayout;
