import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  BadgeCheck,
  Briefcase,
  Building2,
  FileText,
  Server,
  Users,
} from 'lucide-react';

import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import { PageLoader } from '../../components/ui/Spinner';
import { superAdminService } from '../../services/superAdminService';

const EMPTY_METRICS = {
  organizations: { count: 0, growth: 0 },
  users: { count: 0, growth: 0 },
  jobs: { count: 0, growth: 0 },
  applications: { count: 0, growth: 0 },
  revenue: { amount: 0, growth: 0 },
};

const METRIC_CARDS = [
  { key: 'organizations', label: 'Organizations', icon: <Building2 size={22} />, accent: 'bg-sky-50 text-sky-700' },
  { key: 'users', label: 'Active Users', icon: <Users size={22} />, accent: 'bg-emerald-50 text-emerald-700' },
  { key: 'jobs', label: 'Live Jobs', icon: <Briefcase size={22} />, accent: 'bg-amber-50 text-amber-700' },
  { key: 'applications', label: 'Applications', icon: <FileText size={22} />, accent: 'bg-violet-50 text-violet-700' },
];

const HealthPill = ({ label, status }) => (
  <div className="flex items-center justify-between rounded-2xl border border-slate-200 px-4 py-3">
    <span className="text-sm text-slate-600">{label}</span>
    <Badge variant={status === 'healthy' ? 'success' : 'destructive'} size="sm">
      {status}
    </Badge>
  </div>
);

const MetricCard = ({ icon, label, value, growth, accent }) => (
  <Card className="p-5">
    <div className="flex items-start justify-between gap-4">
      <div>
        <p className="text-sm font-medium text-slate-500">{label}</p>
        <p className="mt-2 text-3xl font-bold text-slate-950">{value}</p>
        <p className="mt-2 text-xs font-medium text-slate-500">
          Last 30 days: <span className={growth >= 0 ? 'text-emerald-600' : 'text-rose-600'}>{growth >= 0 ? '+' : ''}{growth}%</span>
        </p>
      </div>
      <div className={`rounded-2xl p-3 ${accent}`}>
        {icon}
      </div>
    </div>
  </Card>
);

const SuperAdminDashboard = () => {
  // Platform snapshot state keeps superadmin data in one predictable place.
  const [dashboard, setDashboard] = useState({
    metrics: EMPTY_METRICS,
    systemHealth: {
      api: 'healthy',
      database: 'healthy',
      email: 'healthy',
      cache: 'healthy',
      storage: 0,
      uptime: 0,
    },
    topOrganizations: [],
    recentActivity: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Initial page load fetches the full dashboard snapshot in parallel.
  useEffect(() => {
    const loadDashboard = async () => {
      setLoading(true);
      setError('');

      try {
        const snapshot = await superAdminService.getDashboardSnapshot();
        setDashboard({
          metrics: { ...EMPTY_METRICS, ...(snapshot.metrics || {}) },
          systemHealth: snapshot.systemHealth || {},
          topOrganizations: snapshot.topOrganizations || [],
          recentActivity: snapshot.recentActivity || [],
        });
      } catch (loadError) {
        setError(loadError.message || 'Unable to load platform dashboard');
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  if (loading) return <PageLoader />;

  return (
    <div className="space-y-6">
      {/* Page header explains the platform-owner scope of this dashboard. */}
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">SaaS ATS Platform</p>
          <h1 className="mt-2 text-3xl font-bold text-slate-950">Superadmin Dashboard</h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-500">
            Manage tenant onboarding, monitor platform health, and keep organization access separated exactly as the multi-tenant architecture requires.
          </p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Link to="/admin/organizations">
            <Button className="w-full justify-center sm:w-auto">
              <Building2 className="mr-2 h-4 w-4" />
              Manage Organizations
            </Button>
          </Link>
        </div>
      </div>

      {/* Error state stays visible without hiding the rest of the page layout. */}
      {error && (
        <Card className="border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          {error}
        </Card>
      )}

      {/* Platform KPI cards summarise the superadmin view at a glance. */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {METRIC_CARDS.map((card) => (
          <MetricCard
            key={card.key}
            icon={card.icon}
            label={card.label}
            accent={card.accent}
            value={dashboard.metrics?.[card.key]?.count ?? 0}
            growth={dashboard.metrics?.[card.key]?.growth ?? 0}
          />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        {/* Top organizations show which tenants are most active right now. */}
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-950">Top Organizations</h2>
              <p className="mt-1 text-sm text-slate-500">Most active tenants by jobs and applications.</p>
            </div>
            <Link to="/admin/organizations" className="text-sm font-medium text-indigo-600 hover:text-indigo-700">
              View all
            </Link>
          </div>

          <div className="mt-6 space-y-3">
            {dashboard.topOrganizations.length === 0 ? (
              <p className="rounded-2xl border border-dashed border-slate-200 px-4 py-8 text-center text-sm text-slate-500">
                No organizations are available yet.
              </p>
            ) : (
              dashboard.topOrganizations.map((organization, index) => (
                <div key={organization.id} className="flex items-center justify-between rounded-2xl border border-slate-200 px-4 py-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-sm font-bold text-slate-700">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-semibold text-slate-900">{organization.name}</p>
                      <p className="text-sm text-slate-500">
                        {organization.jobs_count} jobs • {organization.applications_count} applications
                      </p>
                    </div>
                  </div>
                  <p className="text-sm font-medium text-slate-600">{organization.users_count} users</p>
                </div>
              ))
            )}
          </div>
        </Card>

        {/* System health highlights whether the platform services look healthy. */}
        <Card className="p-6">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl bg-slate-900 p-3 text-white">
              <Server size={20} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-950">System Health</h2>
              <p className="mt-1 text-sm text-slate-500">Operational status for key platform services.</p>
            </div>
          </div>

          <div className="mt-6 space-y-3">
            <HealthPill label="API" status={dashboard.systemHealth.api} />
            <HealthPill label="Database" status={dashboard.systemHealth.database} />
            <HealthPill label="Email" status={dashboard.systemHealth.email} />
            <HealthPill label="Cache" status={dashboard.systemHealth.cache} />
          </div>

          <div className="mt-6 rounded-2xl bg-slate-50 p-4">
            <div className="flex items-center justify-between text-sm text-slate-600">
              <span>Storage usage</span>
              <span>{dashboard.systemHealth.storage ?? 0}%</span>
            </div>
            <div className="mt-3 h-2 rounded-full bg-slate-200">
              <div
                className="h-2 rounded-full bg-slate-900"
                style={{ width: `${dashboard.systemHealth.storage ?? 0}%` }}
              />
            </div>
            <p className="mt-4 text-sm text-slate-600">Uptime: {dashboard.systemHealth.uptime ?? 0}%</p>
          </div>
        </Card>
      </div>

      {/* Recent activity gives the superadmin a lightweight audit snapshot. */}
      <Card className="p-6">
        <div className="flex items-center gap-3">
          <div className="rounded-2xl bg-indigo-50 p-3 text-indigo-700">
            <Activity size={20} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-950">Recent Activity</h2>
            <p className="mt-1 text-sm text-slate-500">Latest tenant onboarding and admin actions.</p>
          </div>
        </div>

        <div className="mt-6 space-y-3">
          {dashboard.recentActivity.length === 0 ? (
            <p className="rounded-2xl border border-dashed border-slate-200 px-4 py-8 text-center text-sm text-slate-500">
              No recent platform activity was found.
            </p>
          ) : (
            dashboard.recentActivity.map((activity, index) => (
              <div key={`${activity.description}-${index}`} className="flex items-start justify-between gap-4 rounded-2xl border border-slate-200 px-4 py-4">
                <div className="flex items-start gap-3">
                  <div className="rounded-2xl bg-emerald-50 p-2 text-emerald-700">
                    <BadgeCheck size={16} />
                  </div>
                  <div>
                    <p className="font-medium text-slate-900">{activity.description}</p>
                    <p className="mt-1 text-sm text-slate-500">{activity.timestamp}</p>
                  </div>
                </div>
                <Badge variant="secondary" size="sm">
                  {activity.type}
                </Badge>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
};

export default SuperAdminDashboard;
