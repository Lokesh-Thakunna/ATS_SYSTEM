import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SearchCheck } from 'lucide-react';
import { jobsService } from '../../services/jobsService';
import { candidateService } from '../../services/candidateService';
import { getApplicationStatusCategory } from '../../services/normalizers';
import { PageLoader } from '../../components/ui/Spinner';
import ApplicationStatusCard from '../../components/candidate/ApplicationStatusCard';

const FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'pending', label: 'Pending' },
  { key: 'reviewing', label: 'Reviewing' },
  { key: 'shortlisted', label: 'Shortlisted' },
  { key: 'rejected', label: 'Rejected' },
];

const MyApplicationsPage = () => {
  const navigate = useNavigate();
  const [applications, setApplications] = useState([]);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState('all');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [applicationsData, profileData] = await Promise.all([
          jobsService.getMyApplications(),
          candidateService.getProfile().catch(() => null),
        ]);
        setApplications(applicationsData.applications || []);
        setProfile(profileData);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const groupedCounts = useMemo(() => applications.reduce((accumulator, application) => {
    const category = getApplicationStatusCategory(application.status);
    accumulator[category] = (accumulator[category] || 0) + 1;
    return accumulator;
  }, {}), [applications]);

  const visibleApplications = useMemo(
    () => applications.filter((application) => activeFilter === 'all' || getApplicationStatusCategory(application.status) === activeFilter),
    [activeFilter, applications],
  );

  if (loading) return <PageLoader />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">My Applications</h1>
        <p className="mt-1 text-sm text-slate-500">Filter, track, and manage all your submitted applications.</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {FILTERS.map((filter) => (
          <button
            key={filter.key}
            type="button"
            onClick={() => setActiveFilter(filter.key)}
            className={`rounded-full border px-4 py-2 text-sm font-medium transition-colors ${
              activeFilter === filter.key
                ? 'border-indigo-200 bg-indigo-50 text-indigo-700'
                : 'border-slate-200 bg-white text-slate-500 hover:border-slate-300'
            }`}
          >
            {filter.label} ({filter.key === 'all' ? applications.length : groupedCounts[filter.key] || 0})
          </button>
        ))}
      </div>

      {visibleApplications.length === 0 ? (
        <div className="surface-panel flex flex-col items-center justify-center px-6 py-16 text-center">
          <SearchCheck size={38} className="text-slate-300" />
          <h2 className="mt-4 text-xl font-semibold text-slate-800">No applications in this view</h2>
          <p className="mt-2 max-w-md text-sm text-slate-500">Start a new application to begin tracking your progress here.</p>
          <button type="button" onClick={() => navigate('/jobs')} className="btn-primary mt-6">
            Browse Jobs
          </button>
        </div>
      ) : (
        <div className="space-y-5">
          {visibleApplications.map((application) => (
            <ApplicationStatusCard
              key={application.id}
              application={application}
              resumeUrl={profile?.resume_url}
              onReapply={() => navigate(`/jobs/${application.job?.id}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default MyApplicationsPage;
