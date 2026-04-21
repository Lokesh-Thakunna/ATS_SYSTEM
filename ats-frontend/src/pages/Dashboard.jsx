import { useAuth } from '../context/AuthContext';
import CandidateDashboard from './candidate/Dashboard';
import RecruiterDashboard from './recruiter/Dashboard';
import AdminOverview from './admin/AdminOverview';
import SuperAdminDashboard from './SuperAdmin/Dashboard';
import { ROLE } from '../utils/roles';

const DASHBOARD_BY_ROLE = {
  [ROLE.SUPER_ADMIN]: SuperAdminDashboard,
  [ROLE.ORG_ADMIN]: AdminOverview,
  [ROLE.RECRUITER]: RecruiterDashboard,
};

const Dashboard = () => {
  const { user } = useAuth();
  const DashboardComponent = DASHBOARD_BY_ROLE[user?.role] || CandidateDashboard;
  return <DashboardComponent />;
};

export default Dashboard;
