import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ArrowRight, Building2, CheckCircle2, Lock, Mail, ShieldCheck, User } from 'lucide-react';
import toast from 'react-hot-toast';

import Spinner from '../../components/ui/Spinner';
import { authService } from '../../services/authService';

const AcceptInvite = () => {
  const { token } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const inviteToken = token || searchParams.get('token') || '';
  const [invite, setInvite] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [form, setForm] = useState({
    full_name: '',
    password: '',
    confirm_password: '',
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    const loadInvite = async () => {
      setLoading(true);
      try {
        if (!inviteToken) {
          throw new Error('Invite token missing');
        }
        const payload = await authService.getOrganizationInviteByToken(inviteToken);
        setInvite(payload);
      } catch (error) {
        toast.error(error.message || 'Invite not found');
      } finally {
        setLoading(false);
      }
    };

    void loadInvite();
  }, [inviteToken]);

  const setField = (key) => (event) => {
    setForm((current) => ({ ...current, [key]: event.target.value }));
    setErrors((current) => ({ ...current, [key]: '' }));
  };

  const validate = () => {
    const nextErrors = {};
    if (!form.full_name.trim()) nextErrors.full_name = 'Full name is required';
    if (!form.password) nextErrors.password = 'Password is required';
    else if (form.password.length < 8 || !/[A-Z]/.test(form.password) || !/[a-z]/.test(form.password) || !/\d/.test(form.password)) {
      nextErrors.password = 'Use at least 8 characters with uppercase, lowercase, and number';
    }
    if (form.password !== form.confirm_password) nextErrors.confirm_password = 'Passwords do not match';
    return nextErrors;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const nextErrors = validate();
    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors);
      return;
    }

    setSubmitting(true);
    try {
      const payload = await authService.acceptOrganizationInvite({
        token: inviteToken,
        full_name: form.full_name,
        password: form.password,
      });
      setInvite((current) => ({ ...current, status: 'accepted' }));
      setShowSuccess(true);
      toast.success('Invite accepted');
      window.setTimeout(() => {
        navigate(`/login?organization_slug=${encodeURIComponent(payload.organization.slug)}`);
      }, 1200);
    } catch (error) {
      toast.error(error.message || 'Failed to accept invite');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!invite) {
    return (
      <div className="card shadow-card-lg text-center">
        <h1 className="text-2xl font-bold text-slate-900">Invite unavailable</h1>
        <p className="mt-2 text-sm text-slate-500">This invite link is missing or no longer valid.</p>
        <Link to="/login" className="btn-primary mt-6 inline-flex justify-center">Go to Sign In</Link>
      </div>
    );
  }

  const isBlocked = invite.status === 'accepted' || invite.status === 'revoked' || invite.is_expired;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">Accept recruiter invite</h1>
        <p className="mt-2 text-gray-500">Join the organization workspace and create your account in one step.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="surface-panel space-y-4 p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500">
              <Building2 size={20} className="text-white" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Organization</p>
              <p className="font-semibold text-slate-900">{invite.organization_name}</p>
            </div>
          </div>

          <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">
            <p className="inline-flex items-center gap-2"><Mail size={14} /> {invite.email}</p>
            <p className="mt-2 inline-flex items-center gap-2"><ShieldCheck size={14} /> Role: {invite.role}</p>
            <p className="mt-2 text-xs text-slate-500">Slug: {invite.organization_slug}</p>
          </div>

          <div className={`rounded-2xl p-4 text-sm ${isBlocked ? 'bg-amber-50 text-amber-800' : 'bg-emerald-50 text-emerald-800'}`}>
            {invite.status === 'accepted' && 'This invite has already been used.'}
            {invite.status === 'revoked' && 'This invite has been revoked by the organization admin.'}
            {invite.is_expired && invite.status !== 'revoked' && invite.status !== 'accepted' && 'This invite has expired. Ask your admin to resend it.'}
            {!isBlocked && 'This invite is active. Complete your account setup below.'}
          </div>
        </div>

        <div className="card shadow-card-lg">
          {showSuccess ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
                <CheckCircle2 size={28} />
              </div>
              <h2 className="mt-4 text-2xl font-bold text-slate-900">Account created</h2>
              <p className="mt-2 text-sm text-slate-500">Redirecting you to sign in for {invite.organization_name}.</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="label">Full name</label>
                <div className="relative">
                  <User size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input type="text" className={`input pl-9 ${errors.full_name ? 'border-red-300 focus:ring-red-400' : ''}`} value={form.full_name} onChange={setField('full_name')} placeholder="Jane Smith" disabled={isBlocked} />
                </div>
                {errors.full_name && <p className="mt-1 text-xs text-red-500">{errors.full_name}</p>}
              </div>

              <div>
                <label className="label">Invite email</label>
                <div className="relative">
                  <Mail size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input type="email" className="input bg-slate-50 pl-9" value={invite.email} disabled />
                </div>
              </div>

              <div>
                <label className="label">Password</label>
                <div className="relative">
                  <Lock size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input type="password" className={`input pl-9 ${errors.password ? 'border-red-300 focus:ring-red-400' : ''}`} value={form.password} onChange={setField('password')} placeholder="Min. 8 characters" disabled={isBlocked} />
                </div>
                {errors.password && <p className="mt-1 text-xs text-red-500">{errors.password}</p>}
              </div>

              <div>
                <label className="label">Confirm password</label>
                <div className="relative">
                  <Lock size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input type="password" className={`input pl-9 ${errors.confirm_password ? 'border-red-300 focus:ring-red-400' : ''}`} value={form.confirm_password} onChange={setField('confirm_password')} placeholder="Repeat password" disabled={isBlocked} />
                </div>
                {errors.confirm_password && <p className="mt-1 text-xs text-red-500">{errors.confirm_password}</p>}
              </div>

              <button type="submit" disabled={submitting || isBlocked} className="btn-primary mt-2 w-full justify-center py-3">
                {submitting ? <Spinner size="sm" /> : <><span>Create Recruiter Account</span><ArrowRight size={16} /></>}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default AcceptInvite;
