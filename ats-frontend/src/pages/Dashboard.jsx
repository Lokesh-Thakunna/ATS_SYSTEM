import { useAuth } from '../context/AuthContext';
import CandidateDashboard from './candidate/CandidateDashboard';
import RecruiterDashboard from './recruiter/RecruiterDashboard';
import AdminOverview from './admin/AdminOverview';

const Dashboard = () => {
  const { user } = useAuth();

  if (user?.role === 'recruiter') return <RecruiterDashboard />;
  if (user?.role === 'admin') return <AdminOverview />;
  return <CandidateDashboard />;
};

export default Dashboard;
