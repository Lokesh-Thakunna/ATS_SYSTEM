import { useAuth } from '../context/AuthContext';
import CandidateDashboard from './candidate/CandidateDashboard';
import RecruiterDashboard from './recruiter/RecruiterDashboard';
import AdminOverview from './admin/AdminOverview';
import SuperAdminDashboard from './SuperAdmin/Dashboard';

const Dashboard = () => {
  const { user } = useAuth();

  if (user?.role === 'recruiter') return <RecruiterDashboard />;
  if (user?.role === 'SUPER_ADMIN') return <SuperAdminDashboard />;
  if (user?.role === 'admin' || user?.role === 'ORG_ADMIN') return <AdminOverview />;
  return <CandidateDashboard />;
};

export default Dashboard;
