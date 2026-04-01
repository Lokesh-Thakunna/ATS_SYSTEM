import { useEffect, useMemo, useState } from 'react';
import { Award, BriefcaseBusiness, FileText, Gauge, Mail, Phone, RefreshCcw, Sparkles, Target, Users } from 'lucide-react';
import toast from 'react-hot-toast';
import { jobsService } from '../../services/jobsService';
import { matchingService } from '../../services/resumeService';
import { normalizeApplicationStatus } from '../../services/normalizers';
import { PageLoader } from '../../components/ui/Spinner';
import { formatDate } from '../../utils/helpers';
import { openAuthenticatedResume } from '../../utils/resumeAccess';

const statusPill = {
  applied: 'bg-amber-50 text-amber-700',
  under_review: 'bg-blue-50 text-blue-700',
  shortlisted: 'bg-emerald-50 text-emerald-700',
  interviewed: 'bg-violet-50 text-violet-700',
  rejected: 'bg-rose-50 text-rose-700',
  hired: 'bg-emerald-50 text-emerald-700',
};

const STATUS_LABELS = {
  applied: 'Applied',
  under_review: 'Under Review',
  shortlisted: 'Shortlisted',
  interviewed: 'Interviewed',
  rejected: 'Rejected',
  hired: 'Hired',
};

const STATUS_ACTIONS = [
  { key: 'under_review', label: 'Mark Review', className: 'btn-secondary' },
  { key: 'shortlisted', label: 'Shortlist', className: 'btn-secondary' },
  { key: 'hired', label: 'Hire', className: 'btn-primary' },
  { key: 'rejected', label: 'Reject', className: 'btn-secondary' },
];

const ScoreBar = ({ label, value, color = 'bg-indigo-500' }) => (
  <div>
    <div className="mb-1 flex items-center justify-between text-xs font-medium text-slate-500">
      <span>{label}</span>
      <span>{Math.round((Number(value) || 0) * 100)}%</span>
    </div>
    <div className="h-2 rounded-full bg-slate-100">
      <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.round((Number(value) || 0) * 100)}%` }} />
    </div>
  </div>
);

const RecruiterApplicantsPage = () => {
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [topN, setTopN] = useState(3);
  const [ranking, setRanking] = useState({ job: null, total_applicants: 0, matches: [] });
  const [loading, setLoading] = useState(true);
  const [rankingLoading, setRankingLoading] = useState(false);
  const [shortlisting, setShortlisting] = useState(false);
  const [statusUpdatingId, setStatusUpdatingId] = useState(null);
  const [resumeOpeningId, setResumeOpeningId] = useState(null);
  const [error, setError] = useState(null);

  const loadJobs = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await jobsService.getRecruiterJobs();
      const nextJobs = response.results || [];
      setJobs(nextJobs);
      setSelectedJobId((current) => current || nextJobs[0]?.id || null);
    } catch (err) {
      setError(err.message || 'Failed to load recruiter jobs');
    } finally {
      setLoading(false);
    }
  };

  const loadRanking = async (jobId, requestedTop = topN) => {
    if (!jobId) {
      setRanking({ job: null, total_applicants: 0, matches: [] });
      return;
    }

    setRankingLoading(true);
    setError(null);
    try {
      const response = await matchingService.matchApplicantsForJob(jobId, requestedTop);
      setRanking(response);
    } catch (err) {
      setError(err.message || 'Failed to calculate applicant ranking');
    } finally {
      setRankingLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, []);

  useEffect(() => {
    if (!selectedJobId) return;
    loadRanking(selectedJobId, topN);
  }, [selectedJobId]);

  const totalApplicantsAcrossJobs = useMemo(
    () => jobs.reduce((sum, job) => sum + (job.applicant_count || 0), 0),
    [jobs],
  );

  const selectedJob = useMemo(
    () => jobs.find((job) => job.id === selectedJobId) || ranking.job,
    [jobs, ranking.job, selectedJobId],
  );

  const handleRefresh = () => {
    loadRanking(selectedJobId, topN);
  };

  const handleShortlistTop = async () => {
    if (!selectedJobId) return;
    setShortlisting(true);
    try {
      const response = await matchingService.shortlistTopCandidatesForJob(selectedJobId, topN);
      toast.success(response.message || 'Top candidates shortlisted');
      await loadRanking(selectedJobId, topN);
    } catch (err) {
      toast.error(err.message || 'Failed to shortlist candidates');
    } finally {
      setShortlisting(false);
    }
  };

  const handleStatusUpdate = async (applicationId, nextStatus) => {
    setStatusUpdatingId(applicationId);
    try {
      const response = await jobsService.updateApplicationStatus(applicationId, nextStatus);
      toast.success(response.message || 'Application status updated');
      await loadRanking(selectedJobId, topN);
    } catch (err) {
      toast.error(err.message || 'Failed to update application status');
    } finally {
      setStatusUpdatingId(null);
    }
  };

  const handleOpenResume = async (applicationId, resumeUrl) => {
    if (!resumeUrl) return;

    setResumeOpeningId(applicationId);
    try {
      await openAuthenticatedResume(resumeUrl);
    } catch (err) {
      toast.error(err.message || 'Unable to open resume');
    } finally {
      setResumeOpeningId(null);
    }
  };

  if (loading) return <PageLoader />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Applicant Matching</h1>
        <p className="mt-1 text-slate-500">Rank applicants against the exact job posting and shortlist the best top N candidates.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="surface-panel flex items-center gap-4 p-5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500">
            <BriefcaseBusiness size={22} className="text-white" />
          </div>
          <div>
            <p className="text-2xl font-bold text-slate-900">{jobs.length}</p>
            <p className="text-sm text-slate-500">My Active Jobs</p>
          </div>
        </div>
        <div className="surface-panel flex items-center gap-4 p-5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500">
            <Users size={22} className="text-white" />
          </div>
          <div>
            <p className="text-2xl font-bold text-slate-900">{totalApplicantsAcrossJobs}</p>
            <p className="text-sm text-slate-500">Applicants On My Jobs</p>
          </div>
        </div>
        <div className="surface-panel flex items-center gap-4 p-5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-500">
            <Target size={22} className="text-white" />
          </div>
          <div>
            <p className="text-2xl font-bold text-slate-900">{ranking.total_applicants || 0}</p>
            <p className="text-sm text-slate-500">Applicants For Selected Job</p>
          </div>
        </div>
      </div>

      {error && (
        <div className="card py-8 text-center">
          <p className="mb-3 text-red-500">{error}</p>
          <button onClick={() => (selectedJobId ? loadRanking(selectedJobId, topN) : loadJobs())} className="btn-secondary">
            Retry
          </button>
        </div>
      )}

      {!error && jobs.length === 0 && (
        <div className="surface-panel py-16 text-center">
          <Sparkles size={40} className="mx-auto mb-3 text-slate-200" />
          <p className="font-medium text-slate-700">You need at least one active job post first</p>
          <p className="mt-1 text-sm text-slate-500">Once candidates apply, this page will rank them automatically.</p>
        </div>
      )}

      {!error && jobs.length > 0 && (
        <>
          <div className="surface-panel p-5">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Choose Job</h2>
                <p className="text-sm text-slate-500">Ranking is calculated from job title, requirements, skills, experience, and candidate application content.</p>
              </div>
              <div className="flex items-center gap-3">
                <label className="text-sm font-medium text-slate-600">Top N</label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={topN}
                  onChange={(event) => setTopN(Math.max(1, Math.min(50, Number(event.target.value) || 1)))}
                  className="input w-24"
                />
                <button onClick={handleRefresh} className="btn-secondary">
                  <RefreshCcw size={14} /> Recalculate
                </button>
                <button onClick={handleShortlistTop} disabled={shortlisting || rankingLoading || !selectedJobId} className="btn-primary">
                  <Award size={14} /> {shortlisting ? 'Shortlisting...' : `Shortlist Top ${topN}`}
                </button>
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {jobs.map((job) => {
                const active = job.id === selectedJobId;
                return (
                  <button
                    key={job.id}
                    type="button"
                    onClick={() => setSelectedJobId(job.id)}
                    className={`rounded-3xl border p-4 text-left transition-all ${
                      active
                        ? 'border-indigo-200 bg-indigo-50 shadow-sm'
                        : 'border-slate-200 bg-white hover:border-slate-300'
                    }`}
                  >
                    <p className="font-semibold text-slate-900">{job.title}</p>
                    <p className="mt-1 text-sm text-slate-500">{job.company || 'Company'} {job.location ? `• ${job.location}` : ''}</p>
                    <p className="mt-3 text-xs font-medium text-slate-500">{job.applicant_count || 0} applicants</p>
                  </button>
                );
              })}
            </div>
          </div>

          {selectedJob && (
            <div className="surface-panel overflow-hidden">
              <div className="border-b border-slate-100 px-6 py-4">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-slate-900">{selectedJob.title}</h2>
                    <p className="mt-1 text-sm text-slate-500">{selectedJob.company || 'Company'} {selectedJob.location ? `• ${selectedJob.location}` : ''}</p>
                  </div>
                  <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-500">
                    <span className="font-medium text-slate-700">{ranking.total_applicants || 0}</span> applicants scored
                  </div>
                </div>
              </div>

              {rankingLoading ? (
                <div className="py-16"><PageLoader /></div>
              ) : ranking.matches?.length > 0 ? (
                <div className="divide-y divide-slate-100">
                  {ranking.matches.map((match, index) => {
                    const normalizedStatus = normalizeApplicationStatus(match.status);

                    return (
                    <div key={match.application_id} className="px-6 py-5">
                      <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
                        <div className="space-y-4 xl:max-w-3xl">
                          <div className="flex flex-wrap items-center gap-3">
                            <span className="inline-flex h-8 min-w-8 items-center justify-center rounded-full bg-indigo-600 px-2 text-xs font-bold text-white">
                              #{index + 1}
                            </span>
                            <h3 className="text-lg font-semibold text-slate-900">{match.candidate.full_name}</h3>
                            <span className={`badge ${statusPill[normalizedStatus] || 'bg-slate-100 text-slate-700'}`}>
                              {STATUS_LABELS[normalizedStatus] || normalizedStatus.replace('_', ' ')}
                            </span>
                            <span className="badge bg-indigo-50 text-indigo-700">{match.fit_label}</span>
                          </div>

                          <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-slate-500">
                            <span className="inline-flex items-center gap-1.5"><Mail size={14} /> {match.candidate.email}</span>
                            {match.candidate.phone && <span className="inline-flex items-center gap-1.5"><Phone size={14} /> {match.candidate.phone}</span>}
                            <span className="inline-flex items-center gap-1.5"><FileText size={14} /> Applied {formatDate(match.applied_at)}</span>
                          </div>

                          {match.candidate.summary && (
                            <p className="text-sm leading-relaxed text-slate-600">{match.candidate.summary}</p>
                          )}

                          <div className="grid gap-3 md:grid-cols-2">
                            <div className="rounded-2xl bg-emerald-50/70 p-4">
                              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-emerald-700">Strengths</p>
                              <div className="space-y-1 text-sm text-emerald-800">
                                {(match.evidence?.strengths || []).length > 0 ? (
                                  match.evidence.strengths.map((item) => <p key={item}>• {item}</p>)
                                ) : (
                                  <p>No standout strengths detected.</p>
                                )}
                              </div>
                            </div>
                            <div className="rounded-2xl bg-rose-50/70 p-4">
                              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-rose-700">Gaps</p>
                              <div className="space-y-1 text-sm text-rose-800">
                                {(match.evidence?.concerns || []).length > 0 ? (
                                  match.evidence.concerns.map((item) => <p key={item}>• {item}</p>)
                                ) : (
                                  <p>No major gaps detected.</p>
                                )}
                              </div>
                            </div>
                          </div>

                          {(match.evidence?.matched_skills?.length > 0 || match.evidence?.missing_skills?.length > 0) && (
                            <div className="grid gap-3 md:grid-cols-2">
                              <div>
                                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Matched Skills</p>
                                <div className="flex flex-wrap gap-2">
                                  {(match.evidence?.matched_skills || []).map((skill) => (
                                    <span key={`${skill.required}-${skill.matched_with}`} className="badge bg-emerald-50 text-emerald-700">
                                      {skill.required}
                                    </span>
                                  ))}
                                </div>
                              </div>
                              <div>
                                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Missing Skills</p>
                                <div className="flex flex-wrap gap-2">
                                  {(match.evidence?.missing_skills || []).map((skill) => (
                                    <span key={skill} className="badge bg-rose-50 text-rose-700">
                                      {skill}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            </div>
                          )}

                          {match.cover_letter && (
                            <div className="rounded-2xl bg-slate-50 p-4">
                              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">Cover Letter</p>
                              <p className="text-sm leading-relaxed text-slate-600">{match.cover_letter}</p>
                            </div>
                          )}
                        </div>

                        <div className="w-full max-w-sm rounded-[28px] border border-slate-100 bg-slate-50/70 p-4">
                          <div className="mb-4 flex items-center justify-between">
                            <div>
                              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Match Score</p>
                              <p className="text-3xl font-bold text-slate-900">{match.score}%</p>
                            </div>
                            <div className="rounded-2xl bg-white px-3 py-2 text-right shadow-sm">
                              <p className="text-xs text-slate-500">Confidence</p>
                              <p className="font-semibold text-slate-800">{Math.round((Number(match.confidence) || 0) * 100)}%</p>
                            </div>
                          </div>

                          <div className="space-y-3">
                            <ScoreBar label="Skills" value={match.component_scores?.skills} color="bg-emerald-500" />
                            <ScoreBar label="Semantic" value={match.component_scores?.semantic} color="bg-indigo-500" />
                            <ScoreBar label="Experience" value={match.component_scores?.experience} color="bg-amber-500" />
                            <ScoreBar label="Title Match" value={match.component_scores?.title} color="bg-sky-500" />
                            <ScoreBar label="Application" value={match.component_scores?.application} color="bg-violet-500" />
                          </div>

                          <div className="mt-4 rounded-2xl bg-white p-4 text-sm text-slate-600">
                            <div className="flex items-center gap-2 font-medium text-slate-800">
                              <Gauge size={15} className="text-indigo-500" />
                              {match.recommendation === 'shortlist' ? 'Recommended for shortlist' : 'Needs recruiter review'}
                            </div>
                            <p className="mt-2">Candidate exp: {match.metrics?.candidate_experience ?? 0} yrs</p>
                            <p>Required exp: {match.metrics?.required_experience ?? 0} yrs</p>
                          </div>

                          <div className="mt-4 grid gap-2">
                            {STATUS_ACTIONS.map((action) => (
                              <button
                                key={action.key}
                                type="button"
                                onClick={() => handleStatusUpdate(match.application_id, action.key)}
                                disabled={statusUpdatingId === match.application_id || normalizedStatus === action.key}
                                className={action.className}
                              >
                                {statusUpdatingId === match.application_id ? 'Updating...' : action.label}
                              </button>
                            ))}
                          </div>

                          {match.candidate.resume_url && (
                            <button
                              type="button"
                              onClick={() => handleOpenResume(match.application_id, match.candidate.resume_url)}
                              className="btn-secondary mt-4 w-full justify-center"
                              disabled={resumeOpeningId === match.application_id}
                            >
                              <FileText size={14} /> Open Resume
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                    );
                  })}
                </div>
              ) : (
                <div className="py-16 text-center">
                  <Users size={40} className="mx-auto mb-3 text-slate-200" />
                  <p className="font-medium text-slate-700">No applicants scored yet</p>
                  <p className="mt-1 text-sm text-slate-500">Applicants will appear here once they apply to this job.</p>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default RecruiterApplicantsPage;
