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
  admin: ROLE.ORG_ADMIN,
};

// Normalize backend and legacy role values into the frontend canonical form.
export const normalizeRole = (role) => {
  if (!role) return ROLE.CANDIDATE;
  const normalized = String(role).trim();
  return ROLE_ALIASES[normalized] || normalized.toLowerCase();
};

// Reusable helpers keep role checks readable inside components.
export const hasRole = (user, roles = []) => roles.includes(normalizeRole(user?.role));
export const isAdminRole = (role) => [ROLE.SUPER_ADMIN, ROLE.ORG_ADMIN].includes(normalizeRole(role));
