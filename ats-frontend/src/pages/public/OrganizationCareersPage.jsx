import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowRight, BriefcaseBusiness, Building2, Globe, Sparkles } from 'lucide-react';

import MarketingFooter from '../../components/shared/MarketingFooter';
import MarketingNavbar from '../../components/shared/MarketingNavbar';
import Spinner from '../../components/ui/Spinner';
import JobList from '../jobs/JobList';
import { authService } from '../../services/authService';

const OrganizationCareersPage = () => {
  const { organizationSlug } = useParams();
  const [organization, setOrganization] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    const loadOrganization = async () => {
      setLoading(true);
      setError('');

      try {
        const payload = await authService.getPublicOrganizationProfile(organizationSlug);
        if (!active) return;
        setOrganization(payload);
      } catch (loadError) {
        if (!active) return;
        setError(loadError.message || 'Organization careers page not found');
      } finally {
        if (active) setLoading(false);
      }
    };

    void loadOrganization();

    return () => {
      active = false;
    };
  }, [organizationSlug]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <MarketingNavbar />
        <div className="flex min-h-[70vh] items-center justify-center">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  if (error || !organization) {
    return (
      <div className="min-h-screen bg-slate-50">
        <MarketingNavbar />
        <main className="mx-auto flex min-h-[70vh] max-w-3xl items-center px-4 py-16 sm:px-6 lg:px-8">
          <div className="w-full rounded-[32px] border border-slate-200 bg-white p-8 text-center shadow-[0_22px_60px_rgba(15,23,42,0.08)]">
            <p className="text-sm font-semibold uppercase tracking-[0.26em] text-slate-400">Careers</p>
            <h1 className="mt-4 text-3xl font-extrabold text-slate-950">This careers page is unavailable</h1>
            <p className="mt-3 text-sm leading-7 text-slate-500">
              {error || 'The organization slug is missing or this team has not enabled its public job board.'}
            </p>
            <Link to="/" className="btn-primary mt-8 inline-flex justify-center">
              Return Home
            </Link>
          </div>
        </main>
        <MarketingFooter />
      </div>
    );
  }

  const accentColor = organization.brand_color || '#0f766e';
  const jobsLabel = organization.open_jobs_count === 1 ? 'open role' : 'open roles';

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#f6fbff_0%,#f8fafc_42%,#ffffff_100%)] text-slate-900">
      <MarketingNavbar />

      <main>
        <section className="relative overflow-hidden">
          <div
            className="absolute inset-x-0 top-0 h-[30rem] opacity-20"
            style={{ background: `radial-gradient(circle at top left, ${accentColor}, transparent 34%)` }}
          />
          <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8 lg:py-20">
            <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
              <div>
                <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/85 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-slate-600 shadow-sm">
                  <Building2 size={14} />
                  {organization.name}
                </div>
                <h1 className="mt-5 max-w-4xl text-4xl font-extrabold leading-tight text-slate-950 sm:text-5xl" style={{ fontFamily: 'Outfit, sans-serif' }}>
                  {organization.careers_page_title}
                </h1>
                <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-600">
                  Explore active roles, learn how this team hires, and jump into the opportunities that match your experience.
                </p>

                <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                  <a href="#open-roles" className="btn-primary justify-center sm:justify-start" style={{ backgroundColor: accentColor, borderColor: accentColor }}>
                    View Open Roles
                    <ArrowRight size={16} />
                  </a>
                  <Link to={`/register?organization_slug=${encodeURIComponent(organization.slug)}`} className="btn-secondary justify-center sm:justify-start">
                    Candidate Sign Up
                  </Link>
                </div>
              </div>

              <div className="rounded-[32px] border border-slate-200 bg-white p-6 shadow-[0_24px_70px_rgba(15,23,42,0.08)]">
                <div className="flex items-center gap-4">
                  {organization.company_logo_url ? (
                    <img
                      src={organization.company_logo_url}
                      alt={`${organization.name} logo`}
                      className="h-16 w-16 rounded-2xl border border-slate-200 object-cover"
                    />
                  ) : (
                    <div className="flex h-16 w-16 items-center justify-center rounded-2xl text-white" style={{ backgroundColor: accentColor }}>
                      <Building2 size={26} />
                    </div>
                  )}
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">Hiring Profile</p>
                    <p className="mt-1 text-2xl font-bold text-slate-950">{organization.name}</p>
                    <p className="mt-1 text-sm text-slate-500">{organization.open_jobs_count} {jobsLabel}</p>
                  </div>
                </div>

                <div className="mt-6 grid gap-4 sm:grid-cols-2">
                  <div className="rounded-[24px] bg-slate-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Workspace</p>
                    <p className="mt-2 inline-flex items-center gap-2 text-sm font-medium text-slate-700">
                      <Sparkles size={15} style={{ color: accentColor }} />
                      {organization.slug}
                    </p>
                  </div>
                  <div className="rounded-[24px] bg-slate-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Timezone</p>
                    <p className="mt-2 inline-flex items-center gap-2 text-sm font-medium text-slate-700">
                      <Globe size={15} style={{ color: accentColor }} />
                      {organization.timezone || 'Default timezone'}
                    </p>
                  </div>
                </div>

                <div className="mt-4 rounded-[24px] bg-slate-950 p-5 text-white">
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-300">Apply Flow</p>
                  <p className="mt-2 text-lg font-bold">Browse publicly, apply once you are ready.</p>
                  <p className="mt-2 text-sm leading-7 text-slate-300">
                    Candidates can review roles here first, then continue with sign-in or registration under the same organization context.
                  </p>
                  <div className="mt-4 flex flex-col gap-3 sm:flex-row">
                    <Link to={`/login?organization_slug=${encodeURIComponent(organization.slug)}`} className="btn-secondary justify-center border-white/20 bg-white/10 text-white hover:bg-white/15">
                      Sign In
                    </Link>
                    <Link to={`/register?organization_slug=${encodeURIComponent(organization.slug)}`} className="btn-primary justify-center" style={{ backgroundColor: accentColor, borderColor: accentColor }}>
                      Register Now
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="open-roles" className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8 lg:pb-24">
          <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em]" style={{ color: accentColor }}>Open Roles</p>
              <h2 className="mt-2 text-3xl font-extrabold text-slate-950" style={{ fontFamily: 'Outfit, sans-serif' }}>
                Hiring now at {organization.name}
              </h2>
            </div>
            <div className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm text-slate-500 shadow-sm">
              <BriefcaseBusiness size={16} style={{ color: accentColor }} />
              Public careers portal
            </div>
          </div>

          <JobList showHeader={false} />
        </section>
      </main>

      <MarketingFooter />
    </div>
  );
};

export default OrganizationCareersPage;
