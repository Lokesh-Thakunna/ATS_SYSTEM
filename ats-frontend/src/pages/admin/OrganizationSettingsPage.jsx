import { useEffect, useState } from 'react';
import { Building2, Globe, Palette, ShieldCheck, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';

import Spinner from '../../components/ui/Spinner';
import { useAuth } from '../../context/AuthContext';
import { authService } from '../../services/authService';
import { formatDate } from '../../utils/helpers';

const initialForm = {
  organization_name: '',
  organization_slug: '',
  organization_email: '',
  organization_password: '',
  company_logo_url: '',
  domain: '',
  timezone: '',
  brand_color: '#4f46e5',
  careers_page_title: '',
  candidate_visibility: 'job_only',
  allow_public_job_board: true,
  auto_publish_jobs: false,
  updated_at: null,
};

const OrganizationSettingsPage = () => {
  const { user, updateUser } = useAuth();
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const setField = (key) => (event) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
    setForm((current) => ({ ...current, [key]: value }));
  };

  const loadSettings = async () => {
    setLoading(true);
    try {
      const payload = await authService.getOrganizationSettings();
      setForm((current) => ({
        ...current,
        ...payload,
        organization_email: payload.organization_email || '',
        organization_password: '', // Don't populate password for security
      }));
    } catch (error) {
      toast.error(error.message || 'Failed to load organization settings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadSettings();
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      const payload = await authService.updateOrganizationSettings({
        organization_name: form.organization_name,
        organization_email: form.organization_email,
        organization_password: form.organization_password,
        company_logo_url: form.company_logo_url,
        domain: form.domain,
        timezone: form.timezone,
        brand_color: form.brand_color,
        careers_page_title: form.careers_page_title,
        candidate_visibility: form.candidate_visibility,
        allow_public_job_board: form.allow_public_job_board,
        auto_publish_jobs: form.auto_publish_jobs,
      });
      setForm((current) => ({ ...current, ...payload }));
      updateUser({
        organization: {
          id: user?.organization?.id ?? null,
          name: payload.organization_name,
          slug: payload.organization_slug,
          email: payload.organization_email,
        },
      });
      toast.success('Organization settings updated');
    } catch (error) {
      toast.error(error.message || 'Failed to update settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">Organization Settings</h1>
          <p className="mt-1 text-slate-500">Manage your workspace identity, visibility rules, and default job publishing behavior.</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-500 shadow-sm">
          Last updated {form.updated_at ? formatDate(form.updated_at) : 'just now'}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="surface-panel flex items-center gap-4 p-5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500">
            <Building2 size={22} className="text-white" />
          </div>
          <div>
            <p className="text-sm text-slate-500">Workspace</p>
            <p className="font-semibold text-slate-900">{form.organization_name || 'Organization'}</p>
            <p className="text-xs text-slate-500">Slug: {form.organization_slug || 'pending'}</p>
          </div>
        </div>

        <div className="surface-panel flex items-center gap-4 p-5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500">
            <Globe size={22} className="text-white" />
          </div>
          <div>
            <p className="text-sm text-slate-500">Public Jobs</p>
            <p className="font-semibold text-slate-900">{form.allow_public_job_board ? 'Enabled' : 'Private'}</p>
            <p className="text-xs text-slate-500">Controls public careers exposure</p>
          </div>
        </div>

        <div className="surface-panel flex items-center gap-4 p-5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl" style={{ backgroundColor: form.brand_color || '#4f46e5' }}>
            <Palette size={22} className="text-white" />
          </div>
          <div>
            <p className="text-sm text-slate-500">Brand Accent</p>
            <p className="font-semibold text-slate-900">{form.brand_color}</p>
            <p className="text-xs text-slate-500">Used for future org branding surfaces</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="surface-panel space-y-5 p-5 sm:p-6">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Organization Profile</h2>
            <p className="mt-1 text-sm text-slate-500">Basic identity details for your ATS workspace and public careers presence.</p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="label">Organization Name</label>
              <input type="text" className="input" value={form.organization_name} onChange={setField('organization_name')} placeholder="Acme Hiring" />
            </div>
            <div>
              <label className="label">Organization Slug</label>
              <input type="text" className="input bg-slate-50" value={form.organization_slug} readOnly />
            </div>
            <div>
              <label className="label">Organization Email</label>
              <input type="email" className="input" value={form.organization_email} onChange={setField('organization_email')} placeholder="admin@acme.com" />
            </div>
            <div>
              <label className="label">Organization Password</label>
              <input type="password" className="input" value={form.organization_password} onChange={setField('organization_password')} placeholder="Enter organization password" />
            </div>
            <div>
              <label className="label">Primary Domain</label>
              <input type="text" className="input" value={form.domain} onChange={setField('domain')} placeholder="careers.acme.com" />
            </div>
            <div>
              <label className="label">Timezone</label>
              <input type="text" className="input" value={form.timezone} onChange={setField('timezone')} placeholder="Asia/Kolkata" />
            </div>
          </div>

          <div>
            <label className="label">Company Logo URL</label>
            <input type="url" className="input" value={form.company_logo_url} onChange={setField('company_logo_url')} placeholder="https://example.com/logo.png" />
          </div>

          <div className="grid gap-4 sm:grid-cols-[1fr_auto]">
            <div>
              <label className="label">Careers Page Title</label>
              <input type="text" className="input" value={form.careers_page_title} onChange={setField('careers_page_title')} placeholder="Join the Acme team" />
            </div>
            <div>
              <label className="label">Brand Color</label>
              <div className="flex items-center gap-3">
                <input type="color" className="h-11 w-14 rounded-xl border border-slate-200 bg-white px-1 py-1" value={form.brand_color} onChange={setField('brand_color')} />
                <input type="text" className="input w-32" value={form.brand_color} onChange={setField('brand_color')} />
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="surface-panel space-y-5 p-5 sm:p-6">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Visibility and Publishing</h2>
              <p className="mt-1 text-sm text-slate-500">Set the default SaaS controls for how candidates and jobs are exposed.</p>
            </div>

            <div>
              <label className="label">Candidate Visibility</label>
              <select className="input" value={form.candidate_visibility} onChange={setField('candidate_visibility')}>
                <option value="job_only">Visible through job applications only</option>
                <option value="private">Private to organization only</option>
              </select>
            </div>

            <label className="flex items-start gap-3 rounded-2xl border border-slate-200 p-4">
              <input type="checkbox" checked={form.allow_public_job_board} onChange={setField('allow_public_job_board')} className="mt-1 h-4 w-4 rounded border-slate-300 text-indigo-600" />
              <span>
                <span className="block font-medium text-slate-900">Enable public job board</span>
                <span className="mt-1 block text-sm text-slate-500">Public org job pages can be exposed when this setting is enabled.</span>
              </span>
            </label>

            <label className="flex items-start gap-3 rounded-2xl border border-slate-200 p-4">
              <input type="checkbox" checked={form.auto_publish_jobs} onChange={setField('auto_publish_jobs')} className="mt-1 h-4 w-4 rounded border-slate-300 text-indigo-600" />
              <span>
                <span className="block font-medium text-slate-900">Auto-publish new jobs</span>
                <span className="mt-1 block text-sm text-slate-500">Turn this on if recruiters should publish immediately instead of saving drafts first.</span>
              </span>
            </label>
          </div>

          <div className="surface-panel space-y-4 p-5 sm:p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-amber-100 text-amber-700">
                <ShieldCheck size={18} />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">Organization Admin Foundation</h3>
                <p className="text-sm text-slate-500">This is the first SaaS admin layer. Billing is intentionally excluded for now.</p>
              </div>
            </div>

            <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">
              <div className="flex items-start gap-2">
                <Sparkles size={16} className="mt-0.5 text-indigo-500" />
                <p>Next non-billing steps can build on this page with recruiter invites, public careers routes, and email verification.</p>
              </div>
            </div>

            <button type="submit" disabled={saving} className="btn-primary w-full justify-center">
              {saving ? <Spinner size="sm" /> : 'Save Settings'}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default OrganizationSettingsPage;
