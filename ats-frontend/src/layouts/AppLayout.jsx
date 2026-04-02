import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from '../components/shared/Navbar';
import Sidebar from '../components/shared/Sidebar';

const AppLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="portal-shell">
      <Navbar
        onMenuToggle={() => setSidebarOpen((current) => !current)}
        menuOpen={sidebarOpen}
      />
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="min-h-screen overflow-x-hidden pt-16 lg:pl-72">
        <div className="mx-auto max-w-[1600px] px-3 py-4 sm:px-5 sm:py-5 lg:px-6 lg:py-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default AppLayout;
