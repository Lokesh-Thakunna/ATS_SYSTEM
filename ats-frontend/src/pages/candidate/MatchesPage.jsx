import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Star, MapPin, DollarSign, ChevronRight, RefreshCw } from 'lucide-react';
import { resumeService, matchingService } from '../../services/resumeService';
import { scoreColor, formatSalary } from '../../utils/helpers';
import { PageLoader } from '../../components/ui/Spinner';

const MatchBar = ({ score }) => (
  <div className="flex items-center gap-2">
    <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
      <div
        className={`h-full rounded-full transition-all ${score >= 80 ? 'bg-emerald-500' : score >= 60 ? 'bg-blue-500' : score >= 40 ? 'bg-amber-500' : 'bg-red-400'}`}
        style={{ width: `${score}%` }}
      />
    </div>
    <span className={`text-xs font-bold px-2 py-0.5 rounded-lg ${scoreColor(score)}`}>{score}%</span>
  </div>
);

const MatchesPage = () => {
  const [matches, setMatches]   = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [resumeId, setResumeId] = useState(null);

  const load = async () => {
    setLoading(true); setError(null);
    try {
      const resumes = await resumeService.getResumes();
      const list = Array.isArray(resumes) ? resumes : resumes.results || [];
      if (!list.length) { setError('no_resume'); setLoading(false); return; }
      const first = list[0];
      setResumeId(first.id);
      const data = await matchingService.matchJobsForResume(first.id);
      setMatches(Array.isArray(data) ? data.slice(0, 20) : []);
    } catch (err) {
      setError(err.message || 'Failed to load matches');
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  if (loading) return <PageLoader />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Job Matches</h1>
          <p className="text-gray-500 mt-1">Top {matches.length} matches based on your resume</p>
        </div>
        <button onClick={load} className="btn-secondary gap-1.5 text-sm">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {error === 'no_resume' && (
        <div className="card text-center py-16">
          <Star size={48} className="mx-auto text-gray-200 mb-3" />
          <p className="font-semibold text-gray-700 mb-2">No resume uploaded yet</p>
          <p className="text-sm text-gray-400 mb-4">Upload your resume to see your top job matches</p>
          <Link to="/resume" className="btn-primary">Upload Resume</Link>
        </div>
      )}

      {error && error !== 'no_resume' && (
        <div className="card border-red-100 text-center py-8">
          <p className="text-red-500 mb-3">{error}</p>
          <button onClick={load} className="btn-secondary">Retry</button>
        </div>
      )}

      {!error && matches.length === 0 && (
        <div className="card text-center py-16">
          <p className="text-gray-500">No matches found yet. Try updating your resume.</p>
        </div>
      )}

      {!error && matches.length > 0 && (
        <div className="space-y-3">
          {matches.map((m, i) => {
            const job = m.job || m;
            return (
              <Link
                key={job.id}
                to={`/jobs/${job.id}`}
                className="card hover:shadow-card-lg hover:-translate-y-0.5 transition-all duration-200 flex items-center gap-4 group"
              >
                {/* Rank */}
                <div className="w-8 h-8 rounded-xl bg-gray-100 flex items-center justify-center text-xs font-bold text-gray-500 shrink-0">
                  #{i + 1}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0 space-y-1">
                  <h3 className="font-semibold text-gray-900 group-hover:text-blue-600 truncate">{job.title}</h3>
                  <p className="text-sm text-gray-500">{job.company}</p>
                  <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-gray-400">
                    {job.location && <span className="flex items-center gap-1"><MapPin size={10} />{job.location}</span>}
                    {(job.salary_min || job.salary_max) && (
                      <span className="flex items-center gap-1"><DollarSign size={10} />{formatSalary(job.salary_min, job.salary_max)}</span>
                    )}
                  </div>
                </div>

                {/* Score */}
                <div className="w-32 shrink-0">
                  <p className="text-[10px] text-gray-400 mb-1 font-medium uppercase tracking-wide">Match</p>
                  <MatchBar score={m.score || 0} />
                </div>

                <ChevronRight size={16} className="text-gray-300 group-hover:text-blue-400 shrink-0" />
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default MatchesPage;
