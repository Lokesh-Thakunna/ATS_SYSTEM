import { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate, Link, useSearchParams } from 'react-router-dom';
import {
  MapPin, DollarSign, Clock, ArrowLeft,
  Send, AlertCircle, FileText, Mail, Phone, CalendarDays,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useJob } from '../../hooks/useJobs';
import { jobsService } from '../../services/jobsService';
import { candidateService } from '../../services/candidateService';
import { formatSalary, timeAgo, jobTypeBadge } from '../../utils/helpers';
import { PageLoader } from '../../components/ui/Spinner';
import Modal from '../../components/ui/Modal';
import Spinner from '../../components/ui/Spinner';
import { useAuth } from '../../context/AuthContext';

const splitName = (fullName = '', email = '') => {
  const parts = fullName.trim().split(/\s+/).filter(Boolean);
  return {
    first_name: parts[0] || email.split('@')[0] || '',
    last_name: parts.slice(1).join(' '),
  };
};

const ApplyModal = ({ open, onClose, jobId, jobTitle }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: user?.email || '',
    phone: '',
    summary: '',
    cover_letter: '',
    expected_salary: '',
    available_from: '',
    resume: null,
  });
  const [loading, setLoading] = useState(false);
  const [profileLoading, setProfileLoading] = useState(false);

  const field = (key) => ({
    value: form[key],
    onChange: (event) => setForm((current) => ({ ...current, [key]: event.target.value })),
  });

  useEffect(() => {
    if (!open) return;

    const loadProfile = async () => {
      setProfileLoading(true);
      try {
        const profile = await candidateService.getProfile().catch(() => null);
        const names = splitName(profile?.full_name || user?.full_name || '', user?.email || '');
        setForm((current) => ({
          ...current,
          first_name: names.first_name,
          last_name: names.last_name,
          email: profile?.email || user?.email || '',
          phone: profile?.phone || '',
          summary: profile?.summary || '',
        }));
      } finally {
        setProfileLoading(false);
      }
    };

    loadProfile();
  }, [open, user]);

  const fullName = useMemo(
    () => `${form.first_name} ${form.last_name}`.trim(),
    [form.first_name, form.last_name],
  );

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!fullName) {
      toast.error('Please add your full name');
      return;
    }

    if (!form.phone.trim()) {
      toast.error('Please add your phone number');
      return;
    }

    if (!form.cover_letter.trim()) {
      toast.error('Please add a cover letter');
      return;
    }

    setLoading(true);
    try {
      await jobsService.applyJob(jobId, {
        full_name: fullName,
        phone: form.phone,
        summary: form.summary,
        cover_letter: form.cover_letter,
        expected_salary: form.expected_salary,
        available_from: form.available_from,
        resume: form.resume,
      });
      toast.success('Application submitted!');
      onClose();
      navigate('/applications');
    } catch (error) {
      toast.error(error.message || 'Application failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title={`Apply for ${jobTitle}`} size="lg">
      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="label">First Name</label>
                <input className="input" placeholder="Swapnil" {...field('first_name')} />
              </div>
              <div>
                <label className="label">Last Name</label>
                <input className="input" placeholder="Chen" {...field('last_name')} />
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="label">Email Address</label>
                <div className="relative">
                  <Mail size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input className="input bg-slate-50 pl-9" readOnly {...field('email')} />
                </div>
              </div>
              <div>
                <label className="label">Phone Number</label>
                <div className="relative">
                  <Phone size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input className="input pl-9" placeholder="8958688502" {...field('phone')} />
                </div>
              </div>
            </div>

            <div>
              <label className="label">Professional Summary</label>
              <textarea
                rows={4}
                className="input resize-none"
                placeholder="Briefly describe your skills and experience..."
                {...field('summary')}
              />
            </div>

            <div>
              <label className="label">Cover Letter</label>
              <textarea
                rows={5}
                className="input resize-none"
                placeholder="Tell the recruiter why you're a great fit for this role..."
                {...field('cover_letter')}
              />
            </div>
          </div>

          <div className="space-y-4">
            <div className="rounded-[24px] border border-indigo-100 bg-indigo-50/70 p-4">
              <p className="text-sm font-semibold text-slate-900">Application Snapshot</p>
              <div className="mt-3 space-y-3 text-sm text-slate-600">
                <div className="flex items-center gap-2"><FileText size={15} className="text-indigo-500" /> {jobTitle}</div>
                <div className="flex items-center gap-2"><CalendarDays size={15} className="text-indigo-500" /> Fast apply with your saved profile</div>
              </div>
            </div>

            <div>
              <label className="label">Expected Salary</label>
              <input className="input" placeholder="e.g. 800000" {...field('expected_salary')} />
            </div>

            <div>
              <label className="label">Available From</label>
              <input type="date" className="input" {...field('available_from')} />
            </div>

            <div>
              <label className="label">Resume</label>
              <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-[22px] border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center">
                <FileText size={22} className="text-slate-400" />
                <span className="text-sm font-medium text-slate-700">
                  {form.resume ? form.resume.name : 'Upload updated resume'}
                </span>
                <span className="text-xs text-slate-400">PDF or DOCX, max 5MB</span>
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  className="hidden"
                  onChange={(event) => setForm((current) => ({ ...current, resume: event.target.files?.[0] || null }))}
                />
              </label>
            </div>

            {profileLoading && <p className="text-xs text-slate-400">Loading saved profile...</p>}
          </div>
        </div>

        <div className="flex flex-col-reverse gap-3 border-t border-slate-100 pt-2 sm:flex-row">
          <button type="submit" disabled={loading || profileLoading} className="btn-primary flex-1 justify-center">
            {loading ? <Spinner size="sm" /> : <><Send size={15} /> Submit Application</>}
          </button>
          <button type="button" onClick={onClose} className="btn-secondary flex-1 justify-center">Cancel</button>
        </div>
      </form>
    </Modal>
  );
};

const JobDetail = () => {
  const { id, organizationSlug: routeOrganizationSlug } = useParams();
  const [searchParams] = useSearchParams();
  const queryOrganizationSlug = searchParams.get('organization_slug') || '';
  const organizationSlug = routeOrganizationSlug || queryOrganizationSlug;
  const { job, loading, error } = useJob(
    id,
    organizationSlug ? { organization_slug: organizationSlug } : {},
  );
  const { user } = useAuth();
  const [applyOpen, setApplyOpen] = useState(false);
  const jobsPath = routeOrganizationSlug
    ? `/careers/${routeOrganizationSlug}`
    : queryOrganizationSlug
      ? `/jobs?organization_slug=${encodeURIComponent(queryOrganizationSlug)}`
      : '/jobs';

  if (loading) return <PageLoader />;

  if (error || !job) {
    return (
      <div className="card py-16 text-center">
        <AlertCircle size={40} className="mx-auto mb-3 text-red-300" />
        <p className="mb-4 text-gray-600">{error || 'Job not found'}</p>
        <Link to={jobsPath} className="btn-secondary">Back to Jobs</Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Link to={jobsPath} className="inline-flex items-center gap-1.5 text-sm text-slate-500 transition-colors hover:text-slate-800">
        <ArrowLeft size={15} /> Back to Jobs
      </Link>

      <div className="surface-panel space-y-6 p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">{job.title}</h1>
            <p className="mt-1 text-slate-500">{job.company}</p>
          </div>
          {job.type && (
            <span className={`badge shrink-0 text-xs font-semibold ${jobTypeBadge(job.type)}`}>
              {job.type}
            </span>
          )}
        </div>

        <div className="flex flex-wrap gap-4 border-y border-slate-100 py-4 text-sm text-slate-500">
          {job.location && (
            <span className="flex items-center gap-1.5"><MapPin size={14} className="text-slate-400" />{job.location}</span>
          )}
          {(job.salary_min || job.salary_max) && (
            <span className="flex items-center gap-1.5"><DollarSign size={14} className="text-slate-400" />{formatSalary(job.salary_min, job.salary_max)}</span>
          )}
          {job.created_at && (
            <span className="flex items-center gap-1.5"><Clock size={14} className="text-slate-400" />Posted {timeAgo(job.created_at)}</span>
          )}
        </div>

        {job.skills?.length > 0 && (
          <div>
            <p className="label">Required Skills</p>
            <div className="flex flex-wrap gap-2">
              {job.skills.map((skill) => (
                <span key={skill} className="badge bg-indigo-50 text-indigo-700 font-medium">{skill}</span>
              ))}
            </div>
          </div>
        )}

        {job.description && (
          <div>
            <p className="label">Job Description</p>
            <div className="whitespace-pre-wrap text-sm leading-relaxed text-slate-600">{job.description}</div>
          </div>
        )}

        {job.requirements && (
          <div>
            <p className="label">Requirements</p>
            <div className="whitespace-pre-wrap text-sm leading-relaxed text-slate-600">{job.requirements}</div>
          </div>
        )}

        {user?.role === 'candidate' && (
          <div className="pt-2">
            <button onClick={() => setApplyOpen(true)} className="btn-primary w-full justify-center py-3 sm:w-auto">
              <Send size={16} /> Apply Now
            </button>
          </div>
        )}
      </div>

      <ApplyModal open={applyOpen} onClose={() => setApplyOpen(false)} jobId={id} jobTitle={job.title} />
    </div>
  );
};

export default JobDetail;
