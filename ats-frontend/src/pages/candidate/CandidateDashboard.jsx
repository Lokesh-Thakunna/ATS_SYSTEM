import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { CalendarDays, FileText, Pencil, Phone, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../../context/AuthContext';
import { candidateService } from '../../services/candidateService';
import { jobsService } from '../../services/jobsService';
import { getApplicationStatusCategory } from '../../services/normalizers';
import { PageLoader } from '../../components/ui/Spinner';
import { formatDate } from '../../utils/helpers';
import ApplicationStatusCard from '../../components/candidate/ApplicationStatusCard';
import EditProfileModal from '../../components/candidate/EditProfileModal';

const StatCard = ({ label, value, color }) => (
  <div className="surface-panel px-5 py-4">
    <p className={`text-3xl font-bold ${color}`}>{value}</p>
    <p className="mt-1 text-sm text-slate-500">{label}</p>
  </div>
);

const splitName = (fullName = '', email = '') => {
  const parts = fullName.trim().split(/\s+/).filter(Boolean);
  return {
    first: parts[0] || email.split('@')[0] || 'Candidate',
    last: parts.slice(1).join(' '),
  };
};

const getProfileStrength = (profile) => {
  if (!profile) return 35;
  const checklist = [
    profile.full_name,
    profile.email,
    profile.phone,
    profile.summary,
    profile.resume_url,
  ];
  return Math.round((checklist.filter(Boolean).length / checklist.length) * 100);
};

const CandidateDashboard = () => {
  const { user, updateUser } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [profile, setProfile] = useState(null);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);

  const editProfileOpen = searchParams.get('editProfile') === '1';

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [profileData, applicationsData] = await Promise.all([
          candidateService.getProfile().catch(() => null),
          jobsService.getMyApplications().catch(() => ({ applications: [] })),
        ]);

        setProfile(profileData);
        setApplications(applicationsData.applications || []);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const names = splitName(profile?.full_name || user?.full_name, user?.email || '');
  const profileStrength = getProfileStrength(profile);
  const recentApplications = applications.slice(0, 2);

  const stats = useMemo(() => {
    const next = {
      total: applications.length,
      pending: 0,
      reviewing: 0,
      shortlisted: 0,
      rejected: 0,
    };

    applications.forEach((application) => {
      next[getApplicationStatusCategory(application.status)] += 1;
    });

    return next;
  }, [applications]);

  const closeProfileModal = () => {
    const next = new URLSearchParams(searchParams);
    next.delete('editProfile');
    setSearchParams(next, { replace: true });
  };

  const openProfileModal = () => {
    const next = new URLSearchParams(searchParams);
    next.set('editProfile', '1');
    setSearchParams(next, { replace: true });
  };

  const handleSaveProfile = async (payload) => {
    setSavingProfile(true);
    try {
      await candidateService.updateProfile(payload);
      const updatedProfile = await candidateService.getProfile();
      setProfile(updatedProfile);
      const updatedNames = splitName(updatedProfile.full_name, updatedProfile.email);
      updateUser({
        first_name: updatedNames.first,
        last_name: updatedNames.last,
        full_name: updatedProfile.full_name,
      });
      toast.success('Profile updated successfully');
      closeProfileModal();
    } catch (error) {
      toast.error(error.message || 'Unable to update profile');
    } finally {
      setSavingProfile(false);
    }
  };

  if (loading) return <PageLoader />;

  return (
    <>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">Welcome back, {names.first}!</h1>
          <p className="mt-1 text-sm text-slate-500">Here's a snapshot of your job search activity.</p>
        </div>

        <div className="surface-panel overflow-hidden">
          <div className="flex flex-col gap-6 px-5 py-5 sm:px-6 xl:flex-row xl:items-center xl:justify-between">
            <div className="flex flex-1 flex-col items-start gap-4 sm:flex-row">
              <div className="flex h-16 w-16 items-center justify-center rounded-full border border-indigo-100 bg-indigo-50 text-2xl font-semibold text-indigo-600">
                {names.first[0]?.toUpperCase()}
              </div>
              <div className="space-y-2">
                <div>
                  <h2 className="text-xl font-semibold text-slate-900">{profile?.full_name || user?.full_name || names.first}</h2>
                  <p className="text-sm text-slate-500">{profile?.email || user?.email}</p>
                </div>

                <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-slate-500">
                  <span className="inline-flex items-center gap-1.5"><Phone size={14} /> {profile?.phone || 'Add your phone number'}</span>
                  <span className="inline-flex items-center gap-1.5"><CalendarDays size={14} /> Joined {formatDate(profile?.created_at)}</span>
                  <span className="inline-flex items-center gap-1.5"><FileText size={14} /> {applications.length} applications</span>
                </div>
              </div>
            </div>

            <div className="flex w-full flex-col gap-3 xl:max-w-xs">
              <div className="flex items-center justify-between text-sm font-medium text-slate-600">
                <span>Profile Strength</span>
                <span className="text-indigo-600">{profileStrength}%</span>
              </div>
              <div className="h-2 rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500"
                  style={{ width: `${profileStrength}%` }}
                />
              </div>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <Link to="/applications" className="text-sm font-medium text-indigo-600 hover:text-indigo-700">
                  View all {'->'}
                </Link>
                <button type="button" onClick={openProfileModal} className="btn-secondary justify-center sm:justify-start">
                  <Pencil size={14} /> Edit Profile
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <StatCard label="Total Applied" value={stats.total} color="text-slate-900" />
          <StatCard label="Pending" value={stats.pending} color="text-amber-500" />
          <StatCard label="Under Review" value={stats.reviewing} color="text-indigo-500" />
          <StatCard label="Shortlisted" value={stats.shortlisted} color="text-emerald-500" />
          <StatCard label="Rejected" value={stats.rejected} color="text-rose-500" />
        </div>

        <div className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Recent Applications</h2>
            <Link to="/applications" className="btn-secondary w-full justify-center px-3 py-2 text-xs sm:w-auto">View all</Link>
          </div>

          {recentApplications.length === 0 ? (
            <div className="surface-panel flex flex-col items-center justify-center px-6 py-16 text-center">
              <Sparkles size={34} className="text-slate-300" />
              <h3 className="mt-4 text-xl font-semibold text-slate-900">No applications yet</h3>
              <p className="mt-2 max-w-md text-sm text-slate-500">Browse open roles and start your first application.</p>
              <button type="button" onClick={() => navigate('/jobs')} className="btn-primary mt-6">
                Find jobs
              </button>
            </div>
          ) : (
            recentApplications.map((application) => (
              <ApplicationStatusCard
                key={application.id}
                application={application}
                resumeUrl={profile?.resume_url}
                onReapply={() => navigate(`/jobs/${application.job?.id}`)}
              />
            ))
          )}
        </div>
      </div>

      <EditProfileModal
        open={editProfileOpen}
        profile={profile || user}
        saving={savingProfile}
        onClose={closeProfileModal}
        onSave={handleSaveProfile}
      />
    </>
  );
};

export default CandidateDashboard;
