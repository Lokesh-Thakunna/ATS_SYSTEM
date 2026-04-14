// Central role map so routing, navigation, and UI badges use one format.
export const ROLE = {
  SUPER_ADMIN: 'super_admin',
  ORG_ADMIN: 'org_admin',
  RECRUITER: 'recruiter',
  CANDIDATE: 'candidate',
};

const ROLE_ALIASES = {
  SUPER_ADMIN: ROLE.SUPER_ADMIN,
  ORG_ADMIN: ROLE.ORG_ADMIN,
  RECRUITER: ROLE.RECRUITER,
  CANDIDATE: ROLE.CANDIDATE,
  superadmin: ROLE.SUPER_ADMIN,
  platform_admin: ROLE.SUPER_ADMIN,
  platformadmin: ROLE.SUPER_ADMIN,
  admin: ROLE.ORG_ADMIN,
};

// Normalize backend and legacy role values into the frontend canonical form.
export const normalizeRole = (role) => {
  if (!role) return null;
  const normalized = String(role).trim();
  return ROLE_ALIASES[normalized] || normalized.toLowerCase();
};

export const resolveUserRole = (user = {}) => {
  const normalizedRole = normalizeRole(user?.role);
  if (user?.is_platform_admin) return ROLE.SUPER_ADMIN;
  return normalizedRole || ROLE.CANDIDATE;
};

// Reusable helpers keep role checks readable inside components.
export const hasRole = (user, roles = []) => Boolean(user) && roles.includes(normalizeRole(user?.role));
export const isAdminRole = (role) => [ROLE.SUPER_ADMIN, ROLE.ORG_ADMIN].includes(normalizeRole(role));
