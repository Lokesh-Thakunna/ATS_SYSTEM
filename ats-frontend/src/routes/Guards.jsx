import { Navigate, Outlet } from 'react-router-dom';
import { normalizeRole } from '../utils/roles';

import { PageLoader } from '../components/ui/Spinner';
import { useAuth } from '../context/AuthContext';

// Protected routes require a valid authenticated session.
export const ProtectedRoute = () => {
  const { user, loading } = useAuth();

  if (loading) return <PageLoader />;
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
};

// Role routes narrow access to the dashboards meant for a specific user type.
export const RoleRoute = ({ roles }) => {
  const { user, loading } = useAuth();

  if (loading) return <PageLoader />;
  if (!user) return <Navigate to="/login" replace />;

  const normalizedRole = normalizeRole(user.role);
  const allowedRoles = roles.map(normalizeRole);
  if (!allowedRoles.includes(normalizedRole)) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
};

// Guest routes keep signed-in users away from login and signup pages.
export const GuestRoute = () => {
  const { user, loading } = useAuth();

  if (loading) return <PageLoader />;
  if (user) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
};
