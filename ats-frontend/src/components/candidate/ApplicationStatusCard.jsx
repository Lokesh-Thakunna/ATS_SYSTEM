import { CalendarDays, MapPin, RotateCcw } from 'lucide-react';

import Badge from '../ui/Badge';
import Card from '../ui/Card';
import { formatDate } from '../../utils/helpers';

const STATUS_VARIANTS = {
  applied: 'secondary',
  under_review: 'warning',
  shortlisted: 'success',
  interviewed: 'secondary',
  hired: 'success',
  rejected: 'destructive',
};

const formatStage = (value) => value ? value.replace(/_/g, ' ') : 'Application submitted';

const ApplicationStatusCard = ({ application, resumeUrl, onReapply }) => (
  <Card className="p-5">
    {/* Job summary section shows the role and employer attached to this application. */}
    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div>
        <div className="flex flex-wrap items-center gap-3">
          <h3 className="text-lg font-semibold text-slate-950">{application.job?.title || 'Untitled role'}</h3>
          <Badge variant={STATUS_VARIANTS[application.status] || 'secondary'} size="sm">
            {application.status_label || formatStage(application.status)}
          </Badge>
        </div>
        <p className="mt-1 text-sm text-slate-500">
          {application.job?.organization_name || application.job?.company || 'Organization not available'}
        </p>
      </div>

      {/* Application meta section keeps important timeline details visible. */}
      <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-slate-500">
        <span className="inline-flex items-center gap-1.5">
          <MapPin size={14} />
          {application.job?.location || 'Location not listed'}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <CalendarDays size={14} />
          Applied {formatDate(application.applied_at)}
        </span>
      </div>
    </div>

    {/* Progress section helps the candidate understand the current application stage. */}
    <div className="mt-5 rounded-2xl bg-slate-50 p-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Current Stage</p>
          <p className="mt-2 text-sm font-medium text-slate-700">{formatStage(application.current_stage || application.status)}</p>
        </div>
        {application.next_stage && (
          <div className="text-sm text-slate-500">
            Next: <span className="font-medium text-slate-700">{formatStage(application.next_stage)}</span>
          </div>
        )}
      </div>

      {application.available_stages?.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {application.available_stages.map((stage) => (
            <span key={stage} className="rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-600">
              {formatStage(stage)}
            </span>
          ))}
        </div>
      )}
    </div>

    {/* Action section provides quick recovery links for resume and re-apply flows. */}
    <div className="mt-5 flex flex-col gap-3 sm:flex-row">
      {resumeUrl && (
        <a href={resumeUrl} target="_blank" rel="noreferrer" className="btn-secondary justify-center">
          View Resume
        </a>
      )}
      {typeof onReapply === 'function' && (
        <button type="button" onClick={onReapply} className="btn-primary justify-center">
          <RotateCcw size={15} />
          Open Job
        </button>
      )}
    </div>
  </Card>
);

export default ApplicationStatusCard;
