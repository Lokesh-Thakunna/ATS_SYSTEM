import { Link } from 'react-router-dom';
import { BriefcaseBusiness, ExternalLink, RefreshCcw } from 'lucide-react';
import toast from 'react-hot-toast';
import { formatDate } from '../../utils/helpers';
import { normalizeApplicationStatus } from '../../services/normalizers';
import { openAuthenticatedResume } from '../../utils/resumeAccess';

const STATUS_META = {
  applied: {
    label: 'Pending',
    pill: 'bg-amber-50 text-amber-700 border border-amber-200',
    stages: ['Applied', 'Reviewing', 'Shortlisted'],
    activeStage: 0,
    accent: 'bg-amber-500',
  },
  under_review: {
    label: 'Reviewing',
    pill: 'bg-sky-50 text-sky-700 border border-sky-200',
    stages: ['Applied', 'Reviewing', 'Shortlisted'],
    activeStage: 1,
    accent: 'bg-sky-500',
  },
  interviewed: {
    label: 'Reviewing',
    pill: 'bg-sky-50 text-sky-700 border border-sky-200',
    stages: ['Applied', 'Reviewing', 'Shortlisted'],
    activeStage: 1,
    accent: 'bg-sky-500',
  },
  shortlisted: {
    label: 'Shortlisted',
    pill: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
    stages: ['Applied', 'Reviewing', 'Shortlisted'],
    activeStage: 2,
    accent: 'bg-emerald-500',
  },
  hired: {
    label: 'Hired',
    pill: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
    stages: ['Applied', 'Reviewing', 'Shortlisted', 'Hired'],
    activeStage: 3,
    accent: 'bg-emerald-500',
  },
  rejected: {
    label: 'Rejected',
    pill: 'bg-rose-50 text-rose-700 border border-rose-200',
    stages: ['Applied', 'Reviewing', 'Rejected'],
    activeStage: 2,
    accent: 'bg-rose-500',
  },
};

const getStatusMeta = (status) => STATUS_META[status] || STATUS_META.applied;

const ProgressNode = ({ label, active, completed, accent }) => (
  <div className="relative flex flex-1 flex-col items-center">
    <div className={`relative z-10 flex h-7 w-7 items-center justify-center rounded-full border text-[11px] font-semibold ${
      completed || active
        ? `${accent} border-transparent text-white shadow-sm`
        : 'border-slate-200 bg-white text-slate-400'
    }`}>
      {completed ? '✓' : label[0]}
    </div>
    <span className={`mt-2 text-[11px] font-medium ${completed || active ? 'text-slate-700' : 'text-slate-400'}`}>
      {label}
    </span>
  </div>
);

const ProgressLine = ({ total, accentClass, activeStage }) => (
  <div className="absolute left-[13%] right-[13%] top-3 h-[2px] rounded-full bg-slate-200">
    <div
      className={`h-full rounded-full ${accentClass}`}
      style={{ width: `${(activeStage / (total - 1)) * 100}%` }}
    />
  </div>
);

const ApplicationStatusCard = ({ application, resumeUrl, onReapply }) => {
  const normalizedStatus = normalizeApplicationStatus(application.status);
  const meta = getStatusMeta(normalizedStatus);
  const tag = application.job?.type || application.job?.location || application.job?.company || application.job?.title;

  const handleOpenResume = async () => {
    try {
      await openAuthenticatedResume(resumeUrl);
    } catch (error) {
      toast.error(error.message || 'Unable to open resume');
    }
  };

  return (
    <div className="surface-panel p-5 sm:p-6">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">{application.job?.title || 'Application'}</h3>
            <p className="mt-1 text-xs text-slate-500">
              Applied {formatDate(application.applied_at)}
            </p>
            <p className="text-xs text-slate-400">
              Last updated {formatDate(application.updated_at || application.applied_at)}
            </p>
          </div>
          <span className={`inline-flex w-fit rounded-full px-3 py-1 text-xs font-semibold ${meta.pill}`}>
            {meta.label}
          </span>
        </div>

        <div className="rounded-3xl border border-slate-100 bg-slate-50/70 p-4">
          <div className="-mx-1 overflow-x-auto px-1">
            <div className="relative flex min-w-[320px] items-start justify-between gap-2 sm:min-w-0">
              <ProgressLine total={meta.stages.length} accentClass={meta.accent} activeStage={meta.activeStage} />
              {meta.stages.map((stage, index) => (
                <ProgressNode
                  key={stage}
                  label={stage}
                  active={index === meta.activeStage}
                  completed={index < meta.activeStage}
                  accent={meta.accent}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-500">
          <div className="flex items-center gap-2">
            <BriefcaseBusiness size={14} className="text-slate-400" />
            <span>{tag || 'Application in progress'}</span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {resumeUrl && (
            <button type="button" onClick={handleOpenResume} className="btn-secondary">
              <ExternalLink size={14} /> View Resume
            </button>
          )}

          {normalizedStatus === 'rejected' && (
            <button type="button" onClick={() => onReapply?.(application)} className="btn-secondary">
              <RefreshCcw size={14} /> Reapply
            </button>
          )}

          {normalizedStatus === 'shortlisted' && (
            <p className="text-sm font-medium text-emerald-600">Congratulations! You've been shortlisted.</p>
          )}

          {normalizedStatus === 'hired' && (
            <p className="text-sm font-medium text-emerald-600">Great news! You've been marked as hired.</p>
          )}

          {(normalizedStatus === 'under_review' || normalizedStatus === 'interviewed') && (
            <Link to={`/jobs/${application.job?.id}`} className="text-sm font-medium text-indigo-600 hover:text-indigo-700">
              View role
            </Link>
          )}
        </div>
      </div>
    </div>
  );
};

export default ApplicationStatusCard;
