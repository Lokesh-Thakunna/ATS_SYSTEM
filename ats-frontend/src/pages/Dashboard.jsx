import { useAuth } from '../context/AuthContext';
import CandidateDashboard from './candidate/CandidateDashboard';
import RecruiterDashboard from './recruiter/RecruiterDashboard';
import AdminDashboard from './admin/AdminDashboard';

const Dashboard = () => {
  const { user } = useAuth();

  if (user?.role === 'recruiter') return <RecruiterDashboard />;
  if (user?.role === 'admin')     return <AdminDashboard />;
  return <CandidateDashboard />;
};

export default Dashboard;
