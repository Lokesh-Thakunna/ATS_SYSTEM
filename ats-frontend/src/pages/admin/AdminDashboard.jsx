import { useEffect, useState } from 'react';
import { ShieldCheck, UserX, PlusCircle, AlertCircle, Building2, Mail, CalendarDays } from 'lucide-react';
import { authService } from '../../services/authService';
import { formatDate } from '../../utils/helpers';
import Modal from '../../components/ui/Modal';
import Spinner from '../../components/ui/Spinner';
import toast from 'react-hot-toast';

const AdminDashboard = () => {
  const [createOpen, setCreateOpen] = useState(false);
  const [recruiters, setRecruiters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [deactivatingId, setDeactivatingId] = useState(null);
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '', company_name: '' });

  const set = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }));

  const loadRecruiters = async () => {
    setLoading(true);
    try {
      const data = await authService.getRecruiters();
      setRecruiters(data);
    } catch (error) {
      toast.error(error.message || 'Failed to load recruiters');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecruiters();
  }, []);

  const handleCreate = async (event) => {
    event.preventDefault();
    if (!form.email || !form.password) {
      toast.error('Email and password required');
      return;
    }

    setSubmitting(true);
    try {
      await authService.createRecruiter({ ...form, role: 'recruiter' });
      toast.success('Recruiter account created!');
      setCreateOpen(false);
      setForm({ first_name: '', last_name: '', email: '', password: '', company_name: '' });
      await loadRecruiters();
    } catch (error) {
      toast.error(error.message || 'Failed to create recruiter');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeactivate = async (userId) => {
    setDeactivatingId(userId);
    try {
      await authService.deactivateRecruiter(userId);
      toast.success('Recruiter deactivated');
      await loadRecruiters();
    } catch (error) {
      toast.error(error.message || 'Failed to deactivate');
    } finally {
      setDeactivatingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">Admin Panel</h1>
          <p className="mt-1 text-slate-500">Manage all active recruiter accounts.</p>
        </div>
        <button onClick={() => setCreateOpen(true)} className="btn-primary w-full justify-center sm:w-auto">
          <PlusCircle size={16} /> Add Recruiter
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="surface-panel flex items-center gap-4 p-5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500">
            <ShieldCheck size={22} className="text-white" />
          </div>
          <div>
            <p className="text-sm text-slate-500">Admin Controls</p>
            <p className="mt-0.5 font-semibold text-slate-800">Full recruiter management access</p>
          </div>
        </div>
        <div className="surface-panel flex items-center gap-4 p-5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500">
            <Building2 size={22} className="text-white" />
          </div>
          <div>
            <p className="text-2xl font-bold text-slate-900">{recruiters.length}</p>
            <p className="text-sm text-slate-500">Active Recruiters</p>
          </div>
        </div>
      </div>

      <div className="surface-panel overflow-hidden">
        <div className="border-b border-slate-100 px-4 py-4 sm:px-6">
          <h2 className="font-semibold text-slate-900">Active Recruiters</h2>
          <p className="mt-1 text-sm text-slate-500">All currently active recruiter accounts are listed here.</p>
        </div>

        {loading ? (
          <div className="flex justify-center px-4 py-12 sm:px-6">
            <Spinner size="md" />
          </div>
        ) : recruiters.length === 0 ? (
          <div className="px-4 py-12 text-center sm:px-6">
            <p className="font-medium text-slate-700">No active recruiters found</p>
            <p className="mt-1 text-sm text-slate-500">Create a recruiter account to get started.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {recruiters.map((recruiter) => (
              <div key={recruiter.id} className="flex flex-col gap-4 px-4 py-5 sm:px-6 lg:flex-row lg:items-center lg:justify-between">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-3">
                    <h3 className="text-lg font-semibold text-slate-900">{recruiter.full_name}</h3>
                    <span className="badge bg-emerald-50 text-emerald-700">Active</span>
                  </div>

                  <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-slate-500">
                    <span className="inline-flex items-center gap-1.5"><Mail size={14} /> {recruiter.email}</span>
                    <span className="inline-flex items-center gap-1.5"><Building2 size={14} /> {recruiter.company_name || 'No company added'}</span>
                    <span className="inline-flex items-center gap-1.5"><CalendarDays size={14} /> Joined {formatDate(recruiter.date_joined)}</span>
                  </div>

                  <p className="text-xs text-slate-400">Recruiter ID: {recruiter.id}</p>
                </div>

                <div className="w-full lg:w-auto">
                  <button
                    type="button"
                    onClick={() => handleDeactivate(recruiter.id)}
                    disabled={deactivatingId === recruiter.id}
                    className="btn-danger w-full justify-center border-red-200 bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 lg:w-auto"
                  >
                    {deactivatingId === recruiter.id ? <Spinner size="sm" /> : <><UserX size={15} /> Deactivate</>}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Create Recruiter Account" size="sm">
        <form onSubmit={handleCreate} className="space-y-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="label">First Name</label>
              <input type="text" className="input" value={form.first_name} onChange={set('first_name')} placeholder="Jane" />
            </div>
            <div>
              <label className="label">Last Name</label>
              <input type="text" className="input" value={form.last_name} onChange={set('last_name')} placeholder="Smith" />
            </div>
          </div>
          <div>
            <label className="label">Company Name</label>
            <input type="text" className="input" value={form.company_name} onChange={set('company_name')} placeholder="ATSSYSTEM" />
          </div>
          <div>
            <label className="label">Email *</label>
            <input type="email" className="input" value={form.email} onChange={set('email')} placeholder="recruiter@company.com" />
          </div>
          <div>
            <label className="label">Temporary Password *</label>
            <input type="password" className="input" value={form.password} onChange={set('password')} placeholder="Min. 8 characters" />
          </div>
          <div className="flex items-center gap-2 rounded-xl bg-amber-50 p-3 text-xs text-amber-700">
            <AlertCircle size={14} className="shrink-0" />
            Share this temporary password securely with the recruiter.
          </div>
          <div className="flex flex-col-reverse gap-3 pt-2 sm:flex-row">
            <button type="button" onClick={() => setCreateOpen(false)} className="btn-secondary flex-1 justify-center">Cancel</button>
            <button type="submit" disabled={submitting} className="btn-primary flex-1 justify-center">
              {submitting ? <Spinner size="sm" /> : 'Create Account'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default AdminDashboard;
