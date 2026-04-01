// Format currency
export const formatSalary = (min, max, currency = 'USD') => {
  const fmt = (n) => new Intl.NumberFormat('en-US', { style: 'currency', currency, maximumFractionDigits: 0 }).format(n);
  if (min && max) return `${fmt(min)} – ${fmt(max)}`;
  if (min) return `From ${fmt(min)}`;
  if (max) return `Up to ${fmt(max)}`;
  return 'Negotiable';
};

// Format date
export const formatDate = (iso) => {
  if (!iso) return '—';
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(iso));
};

// Format relative time
export const timeAgo = (iso) => {
  if (!iso) return '';
  const diff = Date.now() - new Date(iso).getTime();
  const days = Math.floor(diff / 86400000);
  if (days === 0) return 'Today';
  if (days === 1) return 'Yesterday';
  if (days < 7) return `${days}d ago`;
  if (days < 30) return `${Math.floor(days / 7)}w ago`;
  return formatDate(iso);
};

// Match score → color
export const scoreColor = (score) => {
  if (score >= 80) return 'text-emerald-600 bg-emerald-50';
  if (score >= 60) return 'text-blue-600 bg-blue-50';
  if (score >= 40) return 'text-amber-600 bg-amber-50';
  return 'text-red-500 bg-red-50';
};

// File validation
export const validateResumeFile = (file) => {
  const allowed = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
  if (!allowed.includes(file.type)) return 'Only PDF and DOCX files are accepted.';
  if (file.size > 5 * 1024 * 1024) return 'File size must be under 5MB.';
  return null;
};

// Clamp text
export const truncate = (str, n = 120) =>
  str && str.length > n ? str.slice(0, n).trimEnd() + '…' : str;

// Job type badge colours
export const jobTypeBadge = (type) => {
  const map = {
    'full-time':  'bg-blue-50 text-blue-700',
    'part-time':  'bg-purple-50 text-purple-700',
    'contract':   'bg-amber-50 text-amber-700',
    'internship': 'bg-pink-50 text-pink-700',
    'remote':     'bg-teal-50 text-teal-700',
  };
  return map[type?.toLowerCase()] || 'bg-gray-100 text-gray-600';
};
