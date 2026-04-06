const APPLICATION_STATUS_ALIASES = {
  applied: 'applied',
  pending: 'applied',
  under_review: 'under_review',
  review: 'under_review',
  reviewing: 'under_review',
  in_review: 'under_review',
  interviewed: 'interviewed',
  shortlisted: 'shortlisted',
  approved: 'shortlisted',
  selected: 'hired',
  accepted: 'hired',
  hired: 'hired',
  rejected: 'rejected',
};

const normalizeStringList = (values = [], fallbackKeys = []) => {
  if (!Array.isArray(values)) return [];

  const items = values
    .map((value) => {
      if (typeof value === 'string') return value.trim();
      if (value && typeof value === 'object') {
        for (const key of fallbackKeys) {
          if (typeof value[key] === 'string' && value[key].trim()) {
            return value[key].trim();
          }
        }
      }
      return '';
    })
    .filter(Boolean);

  return [...new Set(items)];
};

export const normalizeApplicationStatus = (status) => {
  const normalized = String(status || 'applied').trim().toLowerCase();
  return APPLICATION_STATUS_ALIASES[normalized] || 'applied';
};

export const getApplicationStatusCategory = (status) => {
  const normalized = normalizeApplicationStatus(status);
  if (normalized === 'shortlisted' || normalized === 'hired') return 'shortlisted';
  if (normalized === 'rejected') return 'rejected';
  if (normalized === 'under_review' || normalized === 'interviewed') return 'reviewing';
  return 'pending';
};

export const normalizeUser = (payload = {}) => {
  const fullName = payload.full_name || [payload.first_name, payload.last_name].filter(Boolean).join(' ').trim();

  return {
    id: payload.id ?? payload.user_id ?? null,
    email: payload.email ?? '',
    first_name: payload.first_name ?? fullName.split(' ')[0] ?? '',
    last_name: payload.last_name ?? fullName.split(' ').slice(1).join(' '),
    full_name: fullName || payload.email || '',
    role: payload.role ?? 'candidate',
  };
};

export const normalizeJob = (job = {}) => ({
  ...job,
  company: job.company ?? '',
  type: job.type ?? job.job_type ?? '',
  requirements: job.requirements ?? '',
  skills: Array.isArray(job.skills)
    ? job.skills
    : Array.isArray(job.skills_list)
      ? job.skills_list
      : [],
});

export const normalizeResume = (resume = {}) => ({
  ...resume,
  filename: resume.filename ?? resume.file_name ?? '',
  file_name: resume.file_name ?? resume.filename ?? '',
  resume_url: resume.resume_url ?? resume.access_url ?? resume.url ?? resume.cloud_url ?? '',
  access_url: resume.access_url ?? resume.resume_url ?? resume.url ?? resume.cloud_url ?? '',
  created_at: resume.created_at ?? resume.uploaded_at ?? null,
  uploaded_at: resume.uploaded_at ?? resume.created_at ?? null,
  is_primary: Boolean(resume.is_primary),
  skills: normalizeStringList(resume.skills, ['skill_name', 'name', 'skill']),
  projects: normalizeStringList(resume.projects, ['name', 'title', 'project_name']),
});

export const normalizeMatch = (match = {}) => ({
  ...match,
  score: Number(match.score ?? 0),
  job: match.job ? normalizeJob(match.job) : normalizeJob(match),
});

export const normalizeApplication = (application = {}) => ({
  ...application,
  job: normalizeJob(application.job || {}),
  status: normalizeApplicationStatus(application.status),
  applied_at: application.applied_at || null,
  updated_at: application.updated_at || application.applied_at || null,
});
