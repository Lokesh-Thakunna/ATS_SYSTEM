import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute, GuestRoute, RoleRoute } from './Guards';
import AppLayout from '../layouts/AppLayout';
import AuthLayout from '../layouts/AuthLayout';
import Login from '../pages/auth/Login';
import Register from '../pages/auth/Register';
import AcceptInvite from '../pages/auth/AcceptInvite';
import Dashboard from '../pages/Dashboard';
import ResumePage from '../pages/candidate/ResumePage';
import MatchesPage from '../pages/candidate/MatchesPage';
import MyApplicationsPage from '../pages/candidate/MyApplicationsPage';
import JobList from '../pages/jobs/JobList';
import JobDetail from '../pages/jobs/JobDetail';
import RecruiterDashboard from '../pages/recruiter/RecruiterDashboard';
import RecruiterApplicantsPage from '../pages/recruiter/RecruiterApplicantsPage';
import AdminDashboard from '../pages/admin/AdminDashboard';
import OrganizationSettingsPage from '../pages/admin/OrganizationSettingsPage';
import SuperAdminDashboard from '../pages/SuperAdmin/Dashboard';
import Organizations from '../pages/SuperAdmin/Organizations';
import OrganizationCareersPage from '../pages/public/OrganizationCareersPage';
import OrganizationJobDetailPage from '../pages/public/OrganizationJobDetailPage';

const AppRouter = () => (
  <Routes>
    <Route path="/" element={<Navigate to="/dashboard" replace />} />
    <Route path="/careers/:organizationSlug" element={<OrganizationCareersPage />} />
    <Route path="/careers/:organizationSlug/jobs/:id" element={<OrganizationJobDetailPage />} />

    <Route element={<GuestRoute />}>
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/invites/accept/:token" element={<AcceptInvite />} />
      </Route>
    </Route>

    <Route element={<ProtectedRoute />}>
      <Route element={<AppLayout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/jobs" element={<JobList />} />
        <Route path="/jobs/:id" element={<JobDetail />} />

        <Route element={<RoleRoute roles={['candidate']} />}>
          <Route path="/resume" element={<ResumePage />} />
          <Route path="/matches" element={<MatchesPage />} />
          <Route path="/applications" element={<MyApplicationsPage />} />
        </Route>

        <Route element={<RoleRoute roles={['recruiter']} />}>
          <Route path="/recruiter/jobs" element={<RecruiterDashboard />} />
          <Route path="/recruiter/applicants" element={<RecruiterApplicantsPage />} />
        </Route>

        <Route element={<RoleRoute roles={['admin', 'ORG_ADMIN']} />}>
          <Route path="/admin/recruiters" element={<AdminDashboard />} />
          <Route path="/admin/organization-settings" element={<OrganizationSettingsPage />} />
        </Route>

        <Route element={<RoleRoute roles={['SUPER_ADMIN']} />}>
          <Route path="/admin/organizations" element={<Organizations />} />
        </Route>
      </Route>
    </Route>

    <Route path="*" element={<Navigate to="/dashboard" replace />} />
  </Routes>
);

export default AppRouter;
