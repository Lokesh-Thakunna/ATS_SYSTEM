import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Briefcase, Building2, ChevronRight, ShieldCheck, Users } from 'lucide-react';
import toast from 'react-hot-toast';
import { authService } from '../../services/authService';
import { jobsService } from '../../services/jobsService';
import { PageLoader } from '../../components/ui/Spinner';

const AdminOverview = () => {
  const [loading, setLoading] = useState(true);
  const [recruiterCount, setRecruiterCount] = useState(0);
  const [jobCount, setJobCount] = useState(0);
  const [recentRecruiters, setRecentRecruiters] = useState([]);

  useEffect(() => {
    const loadOverview = async () => {
      setLoading(true);
      try {
        const [recruiters, jobs] = await Promise.all([
          authService.getRecruiters(),
          jobsService.getJobs(),
        ]);

        setRecruiterCount(recruiters.length);
        setRecentRecruiters(recruiters.slice(0, 4));
        setJobCount(jobs.count || jobs.results?.length || 0);
      } catch (error) {
        toast.error(error.message || 'Failed to load admin overview');
      } finally {
        setLoading(false);
      }
    };

    loadOverview();
  }, []);

  if (loading) return <PageLoader />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">Admin Dashboard</h1>
          <p className="mt-1 text-slate-500">Monitor recruiter access and platform activity from one place.</p>
        </div>
        <Link to="/admin/recruiters" className="btn-primary w-full justify-center sm:w-auto">
          <Users size={16} /> Manage Recruiters
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="surface-panel flex items-center gap-4 p-5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500">
            <ShieldCheck size={22} className="text-white" />
          </div>
          <div>
            <p className="text-sm text-slate-500">Admin Access</p>
            <p className="mt-0.5 font-semibold text-slate-800">Recruiter onboarding and control</p>
          </div>
        </div>

        <div className="surface-panel flex items-center gap-4 p-5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500">
            <Building2 size={22} className="text-white" />
          </div>
          <div>
            <p className="text-2xl font-bold text-slate-900">{recruiterCount}</p>
            <p className="text-sm text-slate-500">Active Recruiters</p>
          </div>
        </div>

        <div className="surface-panel flex items-center gap-4 p-5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-500">
            <Briefcase size={22} className="text-white" />
          </div>
          <div>
            <p className="text-2xl font-bold text-slate-900">{jobCount}</p>
            <p className="text-sm text-slate-500">Published Jobs</p>
          </div>
        </div>
      </div>

      <div className="surface-panel overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-100 px-4 py-4 sm:px-6">
          <div>
            <h2 className="font-semibold text-slate-900">Recent Recruiters</h2>
            <p className="mt-1 text-sm text-slate-500">Newest active recruiter accounts on the platform.</p>
          </div>
          <Link to="/admin/recruiters" className="inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:text-indigo-700">
            View all <ChevronRight size={15} />
          </Link>
        </div>

        {recentRecruiters.length === 0 ? (
          <div className="px-4 py-12 text-center text-sm text-slate-500 sm:px-6">
            No recruiter accounts are active yet.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {recentRecruiters.map((recruiter) => (
              <div key={recruiter.id} className="flex flex-col gap-2 px-4 py-4 sm:px-6">
                <p className="font-semibold text-slate-900">{recruiter.full_name}</p>
                <p className="text-sm text-slate-500">{recruiter.email}</p>
                <p className="text-sm text-slate-500">{recruiter.company_name || 'No company added yet'}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminOverview;
