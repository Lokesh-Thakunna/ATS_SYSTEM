import { Link, useSearchParams } from 'react-router-dom';
import { ArrowRight, Building2, Lock, Mail, ShieldCheck } from 'lucide-react';

const OrganizationRegistration = () => {
  const [searchParams] = useSearchParams();
  const organizationSlug = searchParams.get('organization') || '';
  const adminEmail = searchParams.get('email') || '';

  const loginQuery = new URLSearchParams();
  if (organizationSlug) {
    loginQuery.set('organization_slug', organizationSlug);
  }
  if (adminEmail) {
    loginQuery.set('email', adminEmail);
  }

  const loginUrl = `/login${loginQuery.toString() ? `?${loginQuery.toString()}` : ''}`;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">Organization registration</h1>
        <p className="mt-2 text-gray-500">
          Your organization workspace is ready. Sign in with the admin credentials shared in your email.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="surface-panel space-y-4 p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500">
              <Building2 size={20} className="text-white" />
            </div>
            <div>
              <p className="text-sm text-slate-500">Organization slug</p>
              <p className="font-semibold text-slate-900">{organizationSlug || 'Provided in your setup email'}</p>
            </div>
          </div>

          <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">
            <p className="inline-flex items-center gap-2">
              <Mail size={14} /> Admin email: {adminEmail || 'Use email from your setup message'}
            </p>
            <p className="mt-2 inline-flex items-center gap-2">
              <Lock size={14} /> Use temporary password from registration email
            </p>
          </div>

          <div className="rounded-2xl bg-amber-50 p-4 text-sm text-amber-800">
            <p className="inline-flex items-center gap-2">
              <ShieldCheck size={14} /> Security: change your temporary password right after first login.
            </p>
          </div>
        </div>

        <div className="card shadow-card-lg space-y-4">
          <h2 className="text-xl font-semibold text-slate-900">Next steps</h2>
          <ol className="list-decimal space-y-2 pl-5 text-sm text-slate-600">
            <li>Sign in as organization admin.</li>
            <li>Update organization settings and branding.</li>
            <li>Create recruiter invites for your team.</li>
            <li>Post your first job opening.</li>
          </ol>

          <Link to={loginUrl} className="btn-primary mt-4 inline-flex w-full justify-center py-3">
            <span>Go to Sign In</span>
            <ArrowRight size={16} />
          </Link>
        </div>
      </div>
    </div>
  );
};

export default OrganizationRegistration;
