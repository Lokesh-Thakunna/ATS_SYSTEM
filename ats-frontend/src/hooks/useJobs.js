import { useState, useEffect, useCallback, useMemo } from 'react';
import { jobsService } from '../services/jobsService';
import toast from 'react-hot-toast';

const isCanceledRequest = (err) => (
  err?.name === 'AbortError' ||
  err?.code === 'ERR_CANCELED' ||
  err?.type === 'CANCELED'
);

export const useJobs = (params = {}) => {
  const serializedParams = JSON.stringify(params);
  const stableParams = useMemo(() => JSON.parse(serializedParams), [serializedParams]);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchJobs = useCallback(async (config = {}) => {
    setLoading(true);
    setError(null);
    try {
      const data = await jobsService.getJobs(stableParams, config);
      setJobs(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      if (!isCanceledRequest(err)) {
        setError(err.message || 'Failed to load jobs');
      }
    } finally {
      setLoading(false);
    }
  }, [stableParams]);

  useEffect(() => {
    const abortController = new AbortController();
    fetchJobs({ signal: abortController.signal });
    return () => abortController.abort();
  }, [fetchJobs]);

  return { jobs, loading, error, refetch: fetchJobs };
};

export const useJob = (id, params = {}) => {
  const serializedParams = JSON.stringify(params);
  const stableParams = useMemo(() => JSON.parse(serializedParams), [serializedParams]);
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(Boolean(id));
  const [error, setError] = useState(null);

  const fetchJob = useCallback(async (config = {}) => {
    if (!id) {
      setJob(null);
      setError(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const nextJob = await jobsService.getJob(id, stableParams, config);
      setJob(nextJob);
    } catch (err) {
      if (!isCanceledRequest(err)) {
        setError(err.message || 'Failed to load job');
      }
    } finally {
      setLoading(false);
    }
  }, [id, stableParams]);

  useEffect(() => {
    const abortController = new AbortController();
    void fetchJob({ signal: abortController.signal });
    return () => abortController.abort();
  }, [fetchJob]);

  return { job, loading, error };
};

export const useJobMutations = () => {
  const [saving, setSaving] = useState(false);

  const createJob = useCallback(async (data) => {
    setSaving(true);
    try {
      const result = await jobsService.createJob(data);
      toast.success('Job created successfully!');
      return result;
    } catch (err) {
      toast.error(err.message || 'Failed to create job');
      throw err;
    } finally { setSaving(false); }
  }, []);

  const updateJob = useCallback(async (id, data) => {
    setSaving(true);
    try {
      const result = await jobsService.updateJob(id, data);
      toast.success('Job updated!');
      return result;
    } catch (err) {
      toast.error(err.message || 'Failed to update job');
      throw err;
    } finally { setSaving(false); }
  }, []);

  const deleteJob = useCallback(async (id) => {
    setSaving(true);
    try {
      await jobsService.deleteJob(id);
      toast.success('Job deleted');
    } catch (err) {
      toast.error(err.message || 'Failed to delete job');
      throw err;
    } finally {
      setSaving(false);
    }
  }, []);

  return { createJob, updateJob, deleteJob, saving };
};
