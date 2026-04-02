import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, MapPin, DollarSign, Clock, ChevronRight, Briefcase, SlidersHorizontal } from 'lucide-react';
import { useJobs } from '../../hooks/useJobs';
import { formatSalary, timeAgo, jobTypeBadge, truncate } from '../../utils/helpers';
import { PageLoader } from '../../components/ui/Spinner';

const JobCard = ({ job }) => (
  <Link
    to={`/jobs/${job.id}`}
    className="group block card transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card-lg"
  >
    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div className="flex-1 min-w-0">
        {/* Title + company */}
        <h3 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors truncate">
          {job.title}
        </h3>
        <p className="text-sm text-gray-500 mt-0.5">{job.company || 'Company'}</p>

        {/* Meta */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-3 text-xs text-gray-400">
          {job.location && (
            <span className="flex items-center gap-1">
              <MapPin size={11} /> {job.location}
            </span>
          )}
          {(job.salary_min || job.salary_max) && (
            <span className="flex items-center gap-1">
              <DollarSign size={11} /> {formatSalary(job.salary_min, job.salary_max)}
            </span>
          )}
          {job.created_at && (
            <span className="flex items-center gap-1">
              <Clock size={11} /> {timeAgo(job.created_at)}
            </span>
          )}
        </div>

        {/* Description */}
        {job.description && (
          <p className="text-xs text-gray-400 mt-2 leading-relaxed">{truncate(job.description, 100)}</p>
        )}

        {/* Skills */}
        {job.skills?.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {job.skills.slice(0, 5).map((s) => (
              <span key={s} className="badge bg-blue-50 text-blue-600 text-[11px]">{s}</span>
            ))}
            {job.skills.length > 5 && (
              <span className="badge bg-gray-100 text-gray-400 text-[11px]">+{job.skills.length - 5}</span>
            )}
          </div>
        )}
      </div>

      <div className="flex shrink-0 items-center justify-between gap-2 sm:flex-col sm:items-end sm:justify-start">
        {job.type && (
          <span className={`badge text-[11px] font-semibold ${jobTypeBadge(job.type)}`}>
            {job.type}
          </span>
        )}
        <ChevronRight size={18} className="text-gray-300 group-hover:text-blue-400 mt-auto transition-colors" />
      </div>
    </div>
  </Link>
);

const JobList = () => {
  const [filters, setFilters] = useState({ keyword: '', location: '' });
  const [applied, setApplied] = useState({});
  const { jobs, loading, error, refetch } = useJobs(applied);

  const handleSearch = (e) => {
    e.preventDefault();
    setApplied({ ...filters });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">Browse Jobs</h1>
        <p className="text-gray-500 mt-1">{jobs.length} opportunities available</p>
      </div>

      {/* Filters */}
      <form onSubmit={handleSearch} className="card p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Job title or keyword…"
              className="input pl-9"
              value={filters.keyword}
              onChange={(e) => setFilters((p) => ({ ...p, keyword: e.target.value }))}
            />
          </div>
          <div className="relative flex-1">
            <MapPin size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Location…"
              className="input pl-9"
              value={filters.location}
              onChange={(e) => setFilters((p) => ({ ...p, location: e.target.value }))}
            />
          </div>
          <button type="submit" className="btn-primary w-full justify-center shrink-0 sm:w-auto">
            <SlidersHorizontal size={15} /> Filter
          </button>
        </div>
      </form>

      {/* States */}
      {loading && <PageLoader />}

      {error && (
        <div className="card border-red-100 text-center py-8">
          <p className="text-red-500 mb-3">{error}</p>
          <button onClick={refetch} className="btn-secondary">Retry</button>
        </div>
      )}

      {!loading && !error && jobs.length === 0 && (
        <div className="card text-center py-16">
          <Briefcase size={48} className="mx-auto text-gray-200 mb-3" />
          <p className="font-semibold text-gray-600">No jobs found</p>
          <p className="text-sm text-gray-400 mt-1">Try adjusting your filters</p>
        </div>
      )}

      {/* Job cards */}
      {!loading && !error && (
        <div className="space-y-4">
          {jobs.map((job) => <JobCard key={job.id} job={job} />)}
        </div>
      )}
    </div>
  );
};

export default JobList;
