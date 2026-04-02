import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Briefcase, Users, PlusCircle, Edit2, Trash2, Eye, AlertCircle } from 'lucide-react';
import { jobsService } from '../../services/jobsService';
import { useJobMutations } from '../../hooks/useJobs';
import { timeAgo } from '../../utils/helpers';
import { PageLoader } from '../../components/ui/Spinner';
import Modal from '../../components/ui/Modal';
import JobForm from './JobForm';

const MobileJobCard = ({ job, onEdit, onDelete }) => (
  <div className="rounded-[24px] border border-slate-200 bg-white p-4 shadow-sm">
    <div className="flex flex-col gap-3">
      <div>
        <p className="font-semibold text-slate-900">{job.title}</p>
        <p className="mt-1 text-sm text-slate-500">{job.company || 'Company'}</p>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm text-slate-500">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Location</p>
          <p className="mt-1">{job.location || '-'}</p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Applicants</p>
          <p className="mt-1">{job.applicant_count || 0}</p>
        </div>
        <div className="col-span-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Posted</p>
          <p className="mt-1">{timeAgo(job.created_at)}</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <Link to={`/jobs/${job.id}`} className="btn-secondary justify-center px-3">
          <Eye size={15} /> View
        </Link>
        <button onClick={() => onEdit(job)} className="btn-secondary justify-center px-3">
          <Edit2 size={15} /> Edit
        </button>
        <button onClick={() => onDelete(job.id)} className="btn-danger justify-center border-red-200 bg-red-600 px-3 text-white hover:bg-red-700">
          <Trash2 size={15} /> Delete
        </button>
      </div>
    </div>
  </div>
);

const RecruiterDashboard = () => {
  const { deleteJob, saving } = useJobMutations();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editJob, setEditJob] = useState(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [deleteId, setDeleteId] = useState(null);

  const loadJobs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await jobsService.getRecruiterJobs();
      setJobs(data.results || []);
    } catch (err) {
      setError(err.message || 'Failed to load your job postings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, []);

  const totalApplicants = useMemo(
    () => jobs.reduce((sum, job) => sum + (job.applicant_count || 0), 0),
    [jobs],
  );

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await deleteJob(deleteId);
      setDeleteId(null);
      await loadJobs();
    } catch {
      // Deletion errors are already handled in the mutation hook.
    }
  };

  if (loading) return <PageLoader />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">Recruiter Dashboard</h1>
          <p className="mt-1 text-slate-500">Manage only the jobs you have posted.</p>
        </div>
        <button onClick={() => setCreateOpen(true)} className="btn-primary w-full justify-center sm:w-auto">
          <PlusCircle size={16} /> Post a Job
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="surface-panel flex items-center gap-4 p-5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500">
            <Briefcase size={22} className="text-white" />
          </div>
          <div>
            <p className="text-2xl font-bold text-slate-900">{jobs.length}</p>
            <p className="text-sm text-slate-500">My Active Job Postings</p>
          </div>
        </div>
        <div className="surface-panel flex items-center gap-4 p-5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500">
            <Users size={22} className="text-white" />
          </div>
          <div>
            <p className="text-2xl font-bold text-slate-900">{totalApplicants}</p>
            <p className="text-sm text-slate-500">Applicants On My Jobs</p>
          </div>
        </div>
      </div>

      {error && (
        <div className="card border-red-100 py-8 text-center">
          <p className="mb-3 text-red-500">{error}</p>
          <button onClick={loadJobs} className="btn-secondary">Retry</button>
        </div>
      )}

      {!error && (
        <div className="surface-panel overflow-hidden">
          <div className="flex flex-col gap-2 border-b border-slate-100 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
            <h2 className="font-semibold text-slate-900">My Job Postings</h2>
            <Link to="/recruiter/applicants" className="text-sm font-medium text-indigo-600 hover:text-indigo-700">
              View applicants
            </Link>
          </div>
          {jobs.length === 0 ? (
            <div className="py-16 text-center">
              <Briefcase size={40} className="mx-auto mb-3 text-slate-200" />
              <p className="mb-4 text-slate-500">You have not posted any jobs yet</p>
              <button onClick={() => setCreateOpen(true)} className="btn-primary">Post Your First Job</button>
            </div>
          ) : (
            <>
              <div className="space-y-3 p-4 md:hidden">
                {jobs.map((job) => (
                  <MobileJobCard
                    key={job.id}
                    job={job}
                    onEdit={setEditJob}
                    onDelete={setDeleteId}
                  />
                ))}
              </div>

              <div className="hidden overflow-x-auto md:block">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50">
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Title</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 hidden sm:table-cell">Location</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 hidden md:table-cell">Applicants</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 hidden md:table-cell">Posted</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {jobs.map((job) => (
                    <tr key={job.id} className="transition-colors hover:bg-slate-50">
                      <td className="px-6 py-4">
                        <p className="font-medium text-slate-900">{job.title}</p>
                        <p className="text-xs text-slate-400">{job.company}</p>
                      </td>
                      <td className="px-6 py-4 text-slate-500 hidden sm:table-cell">{job.location || '-'}</td>
                      <td className="px-6 py-4 text-slate-500 hidden md:table-cell">{job.applicant_count || 0}</td>
                      <td className="px-6 py-4 text-slate-400 hidden md:table-cell">{timeAgo(job.created_at)}</td>
                      <td className="px-6 py-4">
                        <div className="flex items-center justify-end gap-1">
                          <Link to={`/jobs/${job.id}`} className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-blue-50 hover:text-blue-600" title="View">
                            <Eye size={15} />
                          </Link>
                          <button onClick={() => setEditJob(job)} className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-amber-50 hover:text-amber-600" title="Edit">
                            <Edit2 size={15} />
                          </button>
                          <button onClick={() => setDeleteId(job.id)} className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600" title="Delete">
                            <Trash2 size={15} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              </div>
            </>
          )}
        </div>
      )}

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Post a New Job" size="lg">
        <JobForm onSuccess={() => { setCreateOpen(false); loadJobs(); }} />
      </Modal>

      <Modal open={!!editJob} onClose={() => setEditJob(null)} title="Edit Job" size="lg">
        {editJob && <JobForm job={editJob} onSuccess={() => { setEditJob(null); loadJobs(); }} />}
      </Modal>

      <Modal open={!!deleteId} onClose={() => setDeleteId(null)} title="Delete Job" size="sm">
        <div className="space-y-4">
          <div className="flex items-start gap-3 rounded-xl bg-red-50 p-4">
            <AlertCircle size={18} className="mt-0.5 shrink-0 text-red-500" />
            <p className="text-sm text-red-700">This action cannot be undone. This job and its applications will be removed.</p>
          </div>
          <div className="flex flex-col-reverse gap-3 sm:flex-row">
            <button onClick={() => setDeleteId(null)} className="btn-secondary flex-1 justify-center">Cancel</button>
            <button onClick={handleDelete} disabled={saving} className="btn-danger flex-1 justify-center border-red-200 bg-red-600 text-white hover:bg-red-700">
              Delete Job
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default RecruiterDashboard;
