import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AlertCircle, CheckCircle, ExternalLink, Eye, FileText, RefreshCw, Upload, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { resumeService } from '../../services/resumeService';
import { validateResumeFile } from '../../utils/helpers';
import { getAuthenticatedResumeBlobUrl, openAuthenticatedResume } from '../../utils/resumeAccess';

const isPdfResume = (resume) => {
  const value = `${resume?.mime_type || ''} ${resume?.file_name || ''}`.toLowerCase();
  return value.includes('pdf');
};

const formatFileSize = (bytes) => {
  if (!bytes) return 'Unknown size';
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
};

const ResumePage = () => {
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('idle');
  const [result, setResult] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [resumes, setResumes] = useState([]);
  const [selectedResumeId, setSelectedResumeId] = useState(null);
  const [loadingResumes, setLoadingResumes] = useState(true);
  const [previewUrl, setPreviewUrl] = useState('');
  const [openingResume, setOpeningResume] = useState(false);
  const inputRef = useRef();

  const loadResumes = useCallback(async (preferredResumeId = null) => {
    setLoadingResumes(true);
    try {
      const nextResumes = await resumeService.getResumes();
      setResumes(nextResumes);
      setSelectedResumeId((current) => {
        if (preferredResumeId && nextResumes.some((resume) => resume.id === preferredResumeId)) {
          return preferredResumeId;
        }
        if (current && nextResumes.some((resume) => resume.id === current)) {
          return current;
        }
        return nextResumes.find((resume) => resume.is_primary)?.id || nextResumes[0]?.id || null;
      });
    } catch (err) {
      setResumes([]);
      setSelectedResumeId(null);
      if (err?.status !== 404) {
        toast.error(err.message || 'Unable to load resumes');
      }
    } finally {
      setLoadingResumes(false);
    }
  }, []);

  useEffect(() => {
    loadResumes();
  }, [loadResumes]);

  const selectedResume = useMemo(
    () => resumes.find((resume) => resume.id === selectedResumeId) || resumes[0] || null,
    [resumes, selectedResumeId],
  );

  useEffect(() => {
    let active = true;

    const loadPreview = async () => {
      if (!selectedResume?.resume_url || !isPdfResume(selectedResume)) {
        setPreviewUrl('');
        return;
      }

      try {
        const nextPreviewUrl = await getAuthenticatedResumeBlobUrl(selectedResume.resume_url);
        if (active) {
          setPreviewUrl(nextPreviewUrl);
        }
      } catch (err) {
        if (active) {
          setPreviewUrl('');
          toast.error(err.message || 'Unable to preview resume');
        }
      }
    };

    loadPreview();
    return () => {
      active = false;
    };
  }, [selectedResume]);

  const selectFile = (nextFile) => {
    const err = validateResumeFile(nextFile);
    if (err) {
      toast.error(err);
      return;
    }
    setFile(nextFile);
    setStatus('idle');
    setResult(null);
    setProgress(0);
  };

  const handleDrop = useCallback((event) => {
    event.preventDefault();
    setDragOver(false);
    const droppedFile = event.dataTransfer.files[0];
    if (droppedFile) selectFile(droppedFile);
  }, []);

  const upload = async () => {
    if (!file) return;
    setStatus('uploading');
    setProgress(0);
    try {
      const data = await resumeService.uploadResume(file, setProgress);
      setResult(data);
      setStatus('done');
      await loadResumes(data.resume_id);
      toast.success('Resume uploaded and parsed successfully!');
    } catch (err) {
      setStatus('error');
      toast.error(err.message || 'Upload failed');
    }
  };

  const reset = () => {
    setFile(null);
    setStatus('idle');
    setResult(null);
    setProgress(0);
  };

  const handleOpenResume = async () => {
    if (!selectedResume?.resume_url) return;

    setOpeningResume(true);
    try {
      await openAuthenticatedResume(selectedResume.resume_url);
    } catch (err) {
      toast.error(err.message || 'Unable to open resume');
    } finally {
      setOpeningResume(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">My Resume</h1>
        <p className="mt-1 text-gray-500">Upload, view, and verify the resume that recruiters will see.</p>
      </div>

      <div className="surface-panel p-5 sm:p-6">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Saved Resumes</h2>
            <p className="mt-1 text-sm text-slate-500">Your latest resume is now visible directly in the frontend.</p>
          </div>
          {selectedResume?.resume_url && (
            <button type="button" onClick={handleOpenResume} className="btn-secondary" disabled={openingResume}>
              <ExternalLink size={14} /> Open In New Tab
            </button>
          )}
        </div>

        {loadingResumes ? (
          <div className="rounded-3xl border border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-500">
            Loading your uploaded resume...
          </div>
        ) : resumes.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
            No resume uploaded yet. Upload one below and it will appear here.
          </div>
        ) : (
          <div className="space-y-5">
            <div className="flex flex-wrap gap-2">
              {resumes.map((resume) => (
                <button
                  key={resume.id}
                  type="button"
                  onClick={() => setSelectedResumeId(resume.id)}
                  className={`rounded-full border px-4 py-2 text-sm font-medium transition-colors ${
                    selectedResume?.id === resume.id
                      ? 'border-indigo-200 bg-indigo-50 text-indigo-700'
                      : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
                  }`}
                >
                  {resume.file_name}
                  {resume.is_primary ? ' (Primary)' : ''}
                </button>
              ))}
            </div>

            {selectedResume && (
              <div className="space-y-4">
                <div className="grid gap-4 lg:grid-cols-[1.8fr_1fr]">
                  <div className="rounded-[28px] border border-slate-200 bg-white p-4">
                    <div className="mb-3 flex items-start justify-between gap-3">
                      <div>
                        <p className="text-lg font-semibold text-slate-900">{selectedResume.file_name}</p>
                        <p className="mt-1 text-sm text-slate-500">
                          {formatFileSize(selectedResume.file_size)} • {selectedResume.parsing_status || 'processed'}
                        </p>
                      </div>
                      <span className={`badge ${selectedResume.is_primary ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-700'}`}>
                        {selectedResume.is_primary ? 'Primary Resume' : 'Saved Resume'}
                      </span>
                    </div>

                    {isPdfResume(selectedResume) && previewUrl ? (
                      <iframe
                        title={selectedResume.file_name}
                        src={previewUrl}
                        className="h-[680px] w-full rounded-2xl border border-slate-200"
                      />
                    ) : selectedResume.raw_text ? (
                      <div className="h-[680px] overflow-auto rounded-2xl border border-slate-200 bg-slate-50 p-4">
                        <div className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-700">
                          <Eye size={15} className="text-indigo-500" />
                          Extracted Resume Text Preview
                        </div>
                        <p className="whitespace-pre-wrap text-sm leading-6 text-slate-600">{selectedResume.raw_text}</p>
                      </div>
                    ) : (
                      <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-10 text-center text-sm text-slate-500">
                        Inline preview is best supported for PDFs. Use "Open In New Tab" to inspect this file.
                      </div>
                    )}
                  </div>

                  <div className="space-y-4">
                    <div className="rounded-[28px] border border-slate-200 bg-slate-50 p-4">
                      <p className="text-sm font-semibold text-slate-900">Resume Details</p>
                      <div className="mt-3 space-y-2 text-sm text-slate-600">
                        <p><span className="font-medium text-slate-800">Type:</span> {selectedResume.mime_type || 'Unknown'}</p>
                        <p><span className="font-medium text-slate-800">Projects:</span> {selectedResume.projects?.length || 0}</p>
                        <p><span className="font-medium text-slate-800">Skills:</span> {selectedResume.skills?.length || 0}</p>
                      </div>
                    </div>

                    <div className="rounded-[28px] border border-slate-200 bg-slate-50 p-4">
                      <p className="text-sm font-semibold text-slate-900">Detected Skills</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {selectedResume.skills?.length > 0 ? (
                          selectedResume.skills.map((skill) => (
                            <span key={skill} className="badge bg-indigo-50 text-indigo-700">{skill}</span>
                          ))
                        ) : (
                          <p className="text-sm text-slate-500">No parsed skills available for this resume yet.</p>
                        )}
                      </div>
                    </div>

                    {selectedResume.projects?.length > 0 && (
                      <div className="rounded-[28px] border border-slate-200 bg-slate-50 p-4">
                        <p className="text-sm font-semibold text-slate-900">Projects</p>
                        <div className="mt-3 space-y-2 text-sm text-slate-600">
                          {selectedResume.projects.map((project) => (
                            <p key={project}>• {project}</p>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="surface-panel p-5 sm:p-6">
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-slate-900">Upload New Resume</h2>
          <p className="mt-1 text-sm text-slate-500">PDF resumes preview best here, but DOCX uploads are supported too.</p>
        </div>

        <div
          onDragOver={(event) => { event.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => !file && inputRef.current?.click()}
          className={`
            border-2 border-dashed rounded-2xl p-10 text-center transition-all
            ${dragOver ? 'border-blue-400 bg-blue-50' : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'}
            ${!file ? 'cursor-pointer' : ''}
          `}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            onChange={(event) => event.target.files[0] && selectFile(event.target.files[0])}
          />

          {!file ? (
            <>
              <Upload size={40} className="mx-auto mb-3 text-gray-300" />
              <p className="font-semibold text-gray-700">Drop your resume here or <span className="text-blue-600">browse</span></p>
              <p className="mt-1 text-sm text-gray-400">PDF or DOCX • Max 5MB</p>
            </>
          ) : (
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 shrink-0">
                <FileText size={22} className="text-blue-600" />
              </div>
              <div className="flex-1 text-left">
                <p className="truncate font-semibold text-gray-800">{file.name}</p>
                <p className="text-xs text-gray-400">{formatFileSize(file.size)}</p>
              </div>
              {status === 'idle' && (
                <button onClick={(event) => { event.stopPropagation(); reset(); }} className="rounded-lg p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-500">
                  <X size={16} />
                </button>
              )}
            </div>
          )}
        </div>

        {status === 'uploading' && (
          <div className="card mt-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Uploading and parsing...</span>
              <span className="text-sm font-bold text-blue-600">{progress}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-gray-100">
              <div className="h-full rounded-full bg-blue-500 transition-all duration-300" style={{ width: `${progress}%` }} />
            </div>
            <p className="mt-2 text-xs text-gray-400">Extracting skills and experience...</p>
          </div>
        )}

        {file && status === 'idle' && (
          <button onClick={upload} className="btn-primary mt-4 w-full justify-center py-3">
            <Upload size={16} /> Upload Resume
          </button>
        )}

        {status === 'error' && (
          <div className="card mt-4 flex items-center gap-3 border-red-100 bg-red-50">
            <AlertCircle size={20} className="shrink-0 text-red-500" />
            <p className="flex-1 text-sm text-red-700">Upload failed. Please try again.</p>
            <button onClick={upload} className="btn-secondary gap-1.5 text-xs">
              <RefreshCw size={13} /> Retry
            </button>
          </div>
        )}

        {status === 'done' && result && (
          <div className="card mt-4 space-y-5 border-emerald-100">
            <div className="flex items-center gap-2 text-emerald-700">
              <CheckCircle size={18} />
              <span className="font-semibold">Resume parsed successfully!</span>
            </div>

            {result.skills?.length > 0 && (
              <div>
                <p className="label">Detected Skills</p>
                <div className="flex flex-wrap gap-2">
                  {result.skills.map((skill) => (
                    <span key={skill} className="badge bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">{skill}</span>
                  ))}
                </div>
              </div>
            )}

            {result.experience !== undefined && (
              <div>
                <p className="label">Experience</p>
                <p className="text-sm text-gray-700">{result.experience} years</p>
              </div>
            )}

            {result.match_score !== undefined && result.match_score !== null && (
              <div className="flex items-center gap-3 rounded-xl bg-amber-50 p-3">
                <span className="text-2xl font-bold text-amber-600">{result.match_score}%</span>
                <div>
                  <p className="text-sm font-semibold text-gray-800">Overall Match Score</p>
                  <p className="text-xs text-gray-500">Based on top job listings</p>
                </div>
              </div>
            )}

            <button onClick={reset} className="btn-secondary text-sm">
              <Upload size={14} /> Upload Another
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResumePage;
