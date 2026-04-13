import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Building2 } from 'lucide-react';

import MarketingFooter from '../../components/shared/MarketingFooter';
import MarketingNavbar from '../../components/shared/MarketingNavbar';
import Spinner from '../../components/ui/Spinner';
import JobDetail from '../jobs/JobDetail';
import { authService } from '../../services/authService';

const OrganizationJobDetailPage = () => {
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
            <h1 className="text-3xl font-extrabold text-slate-950">This job page is unavailable</h1>
            <p className="mt-3 text-sm leading-7 text-slate-500">
              {error || 'The public careers portal could not be loaded for this organization.'}
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

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#f8fbff_0%,#ffffff_100%)] text-slate-900">
      <MarketingNavbar />

      <main className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="mb-8 rounded-[32px] border border-slate-200 bg-white p-6 shadow-[0_22px_60px_rgba(15,23,42,0.08)]">
          <Link
            to={`/careers/${organization.slug}`}
            className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 transition-colors hover:text-slate-900"
          >
            <ArrowLeft size={15} />
            Back to {organization.name} careers
          </Link>

          <div className="mt-5 flex items-center gap-4">
            {organization.company_logo_url ? (
              <img
                src={organization.company_logo_url}
                alt={`${organization.name} logo`}
                className="h-14 w-14 rounded-2xl border border-slate-200 object-cover"
              />
            ) : (
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl text-white" style={{ backgroundColor: accentColor }}>
                <Building2 size={24} />
              </div>
            )}
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em]" style={{ color: accentColor }}>Public Job Detail</p>
              <h1 className="mt-1 text-2xl font-extrabold text-slate-950">{organization.name}</h1>
              <p className="mt-1 text-sm text-slate-500">{organization.careers_page_title}</p>
            </div>
          </div>
        </div>

        <JobDetail />
      </main>

      <MarketingFooter />
    </div>
  );
};

export default OrganizationJobDetailPage;
