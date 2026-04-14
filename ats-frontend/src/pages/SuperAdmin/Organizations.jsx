import { useCallback, useEffect, useMemo, useState } from 'react';
import { Building2, Mail, Plus, RefreshCcw, Search, Trash2, Users } from 'lucide-react';
import toast from 'react-hot-toast';

import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import Input from '../../components/ui/Input';
import Modal from '../../components/ui/Modal';
import Spinner, { PageLoader } from '../../components/ui/Spinner';
import { superAdminService } from '../../services/superAdminService';
import { formatDate } from '../../utils/helpers';

const STATUS_OPTIONS = [
  { label: 'All Status', value: 'all' },
  { label: 'Active', value: 'active' },
  { label: 'Inactive', value: 'inactive' },
];

const emptyForm = {
  name: '',
  admin_email: '',
  admin_password: '',
  admin_first_name: '',
  admin_last_name: '',
  website: '',
  industry: '',
  size: '',
};

const statusBadgeVariant = (status) => (status === 'active' ? 'success' : 'secondary');

const Organizations = () => {
  // Page state keeps the tenant list, filters, and modal form isolated.
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [busyOrganizationId, setBusyOrganizationId] = useState(null);

  // Tenant list loader keeps the superadmin page synced with backend data.
  const loadOrganizations = useCallback(async () => {
    setLoading(true);

    try {
      const payload = await superAdminService.getOrganizations({
        status: statusFilter === 'all' ? undefined : statusFilter,
      });
      setOrganizations(payload.results || []);
    } catch (error) {
      toast.error(error.message || 'Unable to load organizations');
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    loadOrganizations();
  }, [loadOrganizations]);

  // Frontend search filtering keeps the page responsive while the API data stays simple.
  const filteredOrganizations = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();
    if (!normalizedSearch) return organizations;

    return organizations.filter((organization) => (
      [organization.name, organization.slug, organization.admin_email]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(normalizedSearch))
    ));
  }, [organizations, searchTerm]);

  const resetForm = () => setForm(emptyForm);

  const handleInputChange = (field) => (event) => {
    setForm((current) => ({ ...current, [field]: event.target.value }));
  };

  // Create organization uses the architecture-approved superadmin onboarding flow.
  const handleCreateOrganization = async (event) => {
    event.preventDefault();
    setSaving(true);

    try {
      await superAdminService.createOrganization(form);
      toast.success('Organization created successfully');
      setCreateOpen(false);
      resetForm();
      await loadOrganizations();
    } catch (error) {
      toast.error(error.message || 'Unable to create organization');
    } finally {
      setSaving(false);
    }
  };

  // Status changes let the superadmin pause or reactivate tenants without deleting data.
  const handleStatusChange = async (organizationId, nextStatus) => {
    setBusyOrganizationId(organizationId);

    try {
      await superAdminService.updateOrganizationStatus(organizationId, nextStatus);
      toast.success(`Organization marked as ${nextStatus}`);
      await loadOrganizations();
    } catch (error) {
      toast.error(error.message || 'Unable to update organization status');
    } finally {
      setBusyOrganizationId(null);
    }
  };

  // Soft delete keeps the tenant record but deactivates the organization access.
  const handleDeactivate = async (organizationId, organizationName) => {
    const shouldContinue = window.confirm(`Deactivate "${organizationName}"? Users in this organization will lose access.`);
    if (!shouldContinue) return;

    setBusyOrganizationId(organizationId);

    try {
      await superAdminService.deleteOrganization(organizationId);
      toast.success('Organization deactivated');
      await loadOrganizations();
    } catch (error) {
      toast.error(error.message || 'Unable to deactivate organization');
    } finally {
      setBusyOrganizationId(null);
    }
  };

  if (loading) return <PageLoader />;

  return (
    <div className="space-y-6">
      {/* Page header explains that this screen controls tenant onboarding. */}
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-400">Tenant Management</p>
          <h1 className="mt-2 text-3xl font-bold text-slate-950">Organizations</h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-500">
            Superadmin creates organizations, assigns the first organization admin, and keeps every tenant isolated from one another.
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)} className="w-full justify-center sm:w-auto">
          <Plus className="mr-2 h-4 w-4" />
          Create Organization
        </Button>
      </div>

      {/* Filter bar controls the visible tenant list. */}
      <Card className="p-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search by organization, slug, or admin email"
              className="pl-10"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            className="input w-full lg:w-48"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>

          <Button variant="outline" onClick={loadOrganizations} className="justify-center">
            <RefreshCcw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </Card>

      {/* Table section shows each organization with its admin and activity counts. */}
      <Card className="overflow-hidden">
        {filteredOrganizations.length === 0 ? (
          <div className="px-6 py-16 text-center">
            <Building2 className="mx-auto h-12 w-12 text-slate-300" />
            <h2 className="mt-4 text-lg font-semibold text-slate-900">No organizations found</h2>
            <p className="mt-2 text-sm text-slate-500">Create the first organization to start the multi-tenant onboarding flow.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Organization</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Admin</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Team</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Jobs</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Applications</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Created</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">Actions</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-100 bg-white">
                {filteredOrganizations.map((organization) => {
                  const busy = busyOrganizationId === organization.id;
                  const nextStatus = organization.status === 'active' ? 'inactive' : 'active';

                  return (
                    <tr key={organization.id} className="hover:bg-slate-50/70">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="rounded-2xl bg-slate-100 p-3 text-slate-700">
                            <Building2 className="h-5 w-5" />
                          </div>
                          <div>
                            <p className="font-semibold text-slate-900">{organization.name}</p>
                            <p className="text-xs text-slate-500">{organization.slug}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="inline-flex items-center gap-2 text-slate-600">
                          <Mail className="h-4 w-4 text-slate-400" />
                          {organization.admin_email || 'Not assigned'}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant={statusBadgeVariant(organization.status)} size="sm">
                          {organization.status}
                        </Badge>
                      </td>
                      <td className="px-6 py-4">
                        <div className="inline-flex items-center gap-2 text-slate-600">
                          <Users className="h-4 w-4 text-slate-400" />
                          {organization.users_count || 0}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-slate-600">{organization.job_count || 0}</td>
                      <td className="px-6 py-4 text-slate-600">{organization.applications_count || 0}</td>
                      <td className="px-6 py-4 text-slate-500">{formatDate(organization.created_at)}</td>
                      <td className="px-6 py-4">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={busy}
                            onClick={() => handleStatusChange(organization.id, nextStatus)}
                          >
                            {busy ? <Spinner size="sm" /> : nextStatus === 'active' ? 'Activate' : 'Pause'}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={busy}
                            onClick={() => handleDeactivate(organization.id, organization.name)}
                            className="text-rose-600 hover:bg-rose-50 hover:text-rose-700"
                          >
                            {busy ? <Spinner size="sm" /> : <Trash2 className="h-4 w-4" />}
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Create modal captures the first admin details for a new tenant. */}
      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Create Organization" size="md">
        <form onSubmit={handleCreateOrganization} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label className="label">Organization Name</label>
              <Input value={form.name} onChange={handleInputChange('name')} placeholder="Acme Technologies" required />
            </div>
            <div className="sm:col-span-2">
              <label className="label">Admin Email</label>
              <Input type="email" value={form.admin_email} onChange={handleInputChange('admin_email')} placeholder="admin@acme.com" required />
            </div>
            <div>
              <label className="label">Admin First Name</label>
              <Input value={form.admin_first_name} onChange={handleInputChange('admin_first_name')} placeholder="Aman" required />
            </div>
            <div>
              <label className="label">Admin Last Name</label>
              <Input value={form.admin_last_name} onChange={handleInputChange('admin_last_name')} placeholder="Sharma" required />
            </div>
            <div className="sm:col-span-2">
              <label className="label">Temporary Password</label>
              <Input type="password" value={form.admin_password} onChange={handleInputChange('admin_password')} placeholder="Minimum 8 characters" required />
            </div>
            <div>
              <label className="label">Website</label>
              <Input value={form.website} onChange={handleInputChange('website')} placeholder="https://acme.com" />
            </div>
            <div>
              <label className="label">Industry</label>
              <Input value={form.industry} onChange={handleInputChange('industry')} placeholder="Technology" />
            </div>
            <div>
              <label className="label">Company Size</label>
              <select value={form.size} onChange={handleInputChange('size')} className="input">
                <option value="">Select size</option>
                <option value="1-10">1-10</option>
                <option value="11-50">11-50</option>
                <option value="51-200">51-200</option>
                <option value="201-500">201-500</option>
                <option value="500+">500+</option>
              </select>
            </div>
          </div>

          <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">
            This flow creates the tenant organization and its first organization admin together, matching the superadmin architecture in your SaaS ATS.
          </div>

          <div className="flex flex-col-reverse gap-3 sm:flex-row">
            <Button type="button" variant="outline" className="w-full justify-center" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" className="w-full justify-center" disabled={saving}>
              {saving ? <Spinner size="sm" /> : 'Create Organization'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Organizations;
