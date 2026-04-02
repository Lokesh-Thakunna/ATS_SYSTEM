import { useState, useEffect, useCallback, useMemo } from 'react';
import { jobsService } from '../services/jobsService';
import toast from 'react-hot-toast';

export const useJobs = (params = {}) => {
  const serializedParams = JSON.stringify(params);
  const stableParams = useMemo(() => JSON.parse(serializedParams), [serializedParams]);
  const [jobs, setJobs]       = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await jobsService.getJobs(stableParams);
      setJobs(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setError(err.message || 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  }, [stableParams]);

  useEffect(() => { fetchJobs(); }, [fetchJobs]);

  return { jobs, loading, error, refetch: fetchJobs };
};

export const useJob = (id) => {
  const [job, setJob]         = useState(null);
  const [loading, setLoading] = useState(Boolean(id));
  const [error, setError]     = useState(null);

  const fetchJob = useCallback(async () => {
    if (!id) {
      setJob(null);
      setError(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const nextJob = await jobsService.getJob(id);
      setJob(nextJob);
    } catch (err) {
      setError(err.message || 'Failed to load job');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void fetchJob();
  }, [fetchJob]);

  return { job, loading, error };
};

export const useJobMutations = () => {
  const [saving, setSaving] = useState(false);

  const createJob = async (data) => {
    setSaving(true);
    try {
      const result = await jobsService.createJob(data);
      toast.success('Job created successfully!');
      return result;
    } catch (err) {
      toast.error(err.message || 'Failed to create job');
      throw err;
    } finally { setSaving(false); }
  };

  const updateJob = async (id, data) => {
    setSaving(true);
    try {
      const result = await jobsService.updateJob(id, data);
      toast.success('Job updated!');
      return result;
    } catch (err) {
      toast.error(err.message || 'Failed to update job');
      throw err;
    } finally { setSaving(false); }
  };

  const deleteJob = async (id) => {
    try {
      await jobsService.deleteJob(id);
      toast.success('Job deleted');
    } catch (err) {
      toast.error(err.message || 'Failed to delete job');
      throw err;
    }
  };

  return { createJob, updateJob, deleteJob, saving };
};
