import { useEffect, useState } from 'react';
import { ShieldCheck, UserX, PlusCircle, AlertCircle, Building2, Mail, CalendarDays, Send, Link as LinkIcon, RotateCcw, Ban } from 'lucide-react';
import { authService } from '../../services/authService';
import { formatDate } from '../../utils/helpers';
import Modal from '../../components/ui/Modal';
import Spinner from '../../components/ui/Spinner';
import toast from 'react-hot-toast';
import { useAuth } from '../../context/AuthContext';

const AdminDashboard = () => {
  const { user } = useAuth();
  const [createOpen, setCreateOpen] = useState(false);
  const [inviteOpen, setInviteOpen] = useState(false);
  const [recruiters, setRecruiters] = useState([]);
  const [invites, setInvites] = useState([]);
  const [organization, setOrganization] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [inviteSubmitting, setInviteSubmitting] = useState(false);
  const [deactivatingId, setDeactivatingId] = useState(null);
  const [inviteActionId, setInviteActionId] = useState(null);
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '' });
  const [inviteForm, setInviteForm] = useState({ email: '', role: 'recruiter' });

  const set = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }));
  const setInvite = (key) => (event) => setInviteForm((current) => ({ ...current, [key]: event.target.value }));

  const loadData = async () => {
    setLoading(true);
    try {
      const [recruiterData, inviteData] = await Promise.all([
        authService.getRecruiters(),
        authService.getOrganizationInvites(),
      ]);
      setRecruiters(Array.isArray(recruiterData?.results) ? recruiterData.results : []);
      setOrganization(recruiterData?.organization || null);
      setInvites(Array.isArray(inviteData?.results) ? inviteData.results : []);
    } catch (error) {
      toast.error(error.message || 'Failed to load admin data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (event) => {
    event.preventDefault();
    const fullName = `${form.first_name} ${form.last_name}`.trim();
    if (!fullName) {
      toast.error('Recruiter full name is required');
      return;
    }

    if (!form.email || !form.password) {
      toast.error('Email and password required');
      return;
    }

    if (form.password.length < 8) {
      toast.error('Temporary password must be at least 8 characters');
      return;
    }

    setSubmitting(true);
    try {
      await authService.createRecruiter({ ...form, role: 'recruiter' });
      toast.success('Recruiter account created!');
      setCreateOpen(false);
      setForm({ first_name: '', last_name: '', email: '', password: '' });
      await loadData();
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
      await loadData();
    } catch (error) {
      toast.error(error.message || 'Failed to deactivate');
    } finally {
      setDeactivatingId(null);
    }
  };

  const handleInviteCreate = async (event) => {
    event.preventDefault();
    if (!inviteForm.email) {
      toast.error('Invite email is required');
      return;
    }

    setInviteSubmitting(true);
    try {
      const invite = await authService.createOrganizationInvite(inviteForm);
      toast.success('Invite created');
      await navigator.clipboard.writeText(`${window.location.origin}${invite.invite_link}`);
      toast.success('Invite link copied');
      setInviteOpen(false);
      setInviteForm({ email: '', role: 'recruiter' });
      await loadData();
    } catch (error) {
      toast.error(error.message || 'Failed to create invite');
    } finally {
      setInviteSubmitting(false);
    }
  };

  const handleInviteAction = async (inviteId, action) => {
    setInviteActionId(inviteId);
    try {
      const invite = action === 'resend'
        ? await authService.resendOrganizationInvite(inviteId)
        : await authService.revokeOrganizationInvite(inviteId);

      if (action === 'resend') {
        await navigator.clipboard.writeText(`${window.location.origin}${invite.invite_link}`);
        toast.success('Invite resent and link copied');
      } else {
        toast.success('Invite revoked');
      }
      await loadData();
    } catch (error) {
      toast.error(error.message || `Failed to ${action} invite`);
    } finally {
      setInviteActionId(null);
    }
  };

  const copyInviteLink = async (invite) => {
    try {
      await navigator.clipboard.writeText(`${window.location.origin}${invite.invite_link}`);
      toast.success('Invite link copied');
    } catch {
      toast.error('Failed to copy invite link');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">
            {user?.is_platform_admin ? 'Platform Admin Recruiters' : 'Organization Admin Panel'}
          </h1>
          <p className="mt-1 text-slate-500">
            Manage recruiter accounts for {organization?.name || 'your organization'}.
          </p>
          <p className="mt-1 text-sm text-slate-500">
            Only organization admins can create or invite recruiters. Recruiters cannot create organizations or additional recruiter accounts.
          </p>
        </div>
        <button onClick={() => setCreateOpen(true)} className="btn-primary w-full justify-center sm:w-auto">
          <PlusCircle size={16} /> Add Recruiter
        </button>
        <button onClick={() => setInviteOpen(true)} className="btn-secondary w-full justify-center sm:w-auto">
          <Send size={16} /> Invite Recruiter
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="surface-panel flex items-center gap-4 p-5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500">
            <ShieldCheck size={22} className="text-white" />
          </div>
          <div>
            <p className="text-sm text-slate-500">Access Model</p>
            <p className="mt-0.5 font-semibold text-slate-800">Organization admins onboard recruiters</p>
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
          <p className="mt-1 text-sm text-slate-500">Only recruiters from your current organization are listed here.</p>
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
                    <span className="inline-flex items-center gap-1.5"><Building2 size={14} /> {recruiter.organization_name || recruiter.company_name || 'Organization not assigned'}</span>
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

      <div className="surface-panel overflow-hidden">
        <div className="border-b border-slate-100 px-4 py-4 sm:px-6">
          <h2 className="font-semibold text-slate-900">Pending and Recent Invites</h2>
          <p className="mt-1 text-sm text-slate-500">Share invite links now. Recruiters join the existing organization through this flow instead of creating their own workspace.</p>
        </div>

        {loading ? (
          <div className="flex justify-center px-4 py-12 sm:px-6">
            <Spinner size="md" />
          </div>
        ) : invites.length === 0 ? (
          <div className="px-4 py-12 text-center sm:px-6">
            <p className="font-medium text-slate-700">No invites created yet</p>
            <p className="mt-1 text-sm text-slate-500">Create an invite to onboard recruiters without manually sharing passwords.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {invites.map((invite) => (
              <div key={invite.id} className="flex flex-col gap-4 px-4 py-5 sm:px-6 lg:flex-row lg:items-center lg:justify-between">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-3">
                    <h3 className="text-lg font-semibold text-slate-900">{invite.email}</h3>
                    <span className={`badge ${invite.status === 'accepted' ? 'bg-emerald-50 text-emerald-700' : invite.status === 'revoked' ? 'bg-rose-50 text-rose-700' : invite.is_expired ? 'bg-amber-50 text-amber-700' : 'bg-indigo-50 text-indigo-700'}`}>
                      {invite.is_expired && invite.status === 'pending' ? 'expired' : invite.status}
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-slate-500">
                    <span className="inline-flex items-center gap-1.5"><Mail size={14} /> {invite.role}</span>
                    <span className="inline-flex items-center gap-1.5"><CalendarDays size={14} /> Expires {formatDate(invite.expires_at)}</span>
                    <span className="inline-flex items-center gap-1.5"><ShieldCheck size={14} /> Invited by {invite.invited_by_name || 'Admin'}</span>
                  </div>
                </div>

                <div className="flex flex-col gap-2 sm:flex-row">
                  <button type="button" onClick={() => copyInviteLink(invite)} className="btn-secondary justify-center">
                    <LinkIcon size={15} /> Copy Link
                  </button>
                  {invite.status !== 'accepted' && invite.status !== 'revoked' && (
                    <>
                      <button
                        type="button"
                        onClick={() => handleInviteAction(invite.id, 'resend')}
                        disabled={inviteActionId === invite.id}
                        className="btn-secondary justify-center"
                      >
                        {inviteActionId === invite.id ? <Spinner size="sm" /> : <><RotateCcw size={15} /> Resend</>}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleInviteAction(invite.id, 'revoke')}
                        disabled={inviteActionId === invite.id}
                        className="btn-danger justify-center border-red-200 bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
                      >
                        {inviteActionId === invite.id ? <Spinner size="sm" /> : <><Ban size={15} /> Revoke</>}
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Create Recruiter Account" size="sm">
        <form onSubmit={handleCreate} className="space-y-4">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Organization Scope</p>
            <p className="mt-2 inline-flex items-center gap-2 text-sm font-medium text-slate-700">
              <Building2 size={15} />
              {organization?.name || 'Your current organization'}
            </p>
            <p className="mt-2 text-xs text-slate-500">New recruiters will be created inside this organization only. Organization creation stays with platform setup, not recruiter signup.</p>
          </div>
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

      <Modal open={inviteOpen} onClose={() => setInviteOpen(false)} title="Invite Recruiter" size="sm">
        <form onSubmit={handleInviteCreate} className="space-y-4">
          <div>
            <label className="label">Recruiter Email *</label>
            <input type="email" className="input" value={inviteForm.email} onChange={setInvite('email')} placeholder="recruiter@company.com" />
          </div>
          <div>
            <label className="label">Role</label>
            <select className="input" value={inviteForm.role} onChange={setInvite('role')}>
              <option value="recruiter">Recruiter</option>
            </select>
          </div>
          <div className="flex items-center gap-2 rounded-xl bg-cyan-50 p-3 text-xs text-cyan-700">
            <AlertCircle size={14} className="shrink-0" />
            This MVP copies a secure invite link after creation. Email sending can be added later.
          </div>
          <div className="flex flex-col-reverse gap-3 pt-2 sm:flex-row">
            <button type="button" onClick={() => setInviteOpen(false)} className="btn-secondary flex-1 justify-center">Cancel</button>
            <button type="submit" disabled={inviteSubmitting} className="btn-primary flex-1 justify-center">
              {inviteSubmitting ? <Spinner size="sm" /> : 'Create Invite'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default AdminDashboard;
