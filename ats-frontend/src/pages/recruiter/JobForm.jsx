import { useState } from 'react';
import { useJobMutations } from '../../hooks/useJobs';
import Spinner from '../../components/ui/Spinner';

const TYPES = ['Full-time', 'Part-time', 'Contract', 'Internship', 'Remote'];

const JobForm = ({ job, onSuccess }) => {
  const { createJob, updateJob, saving } = useJobMutations();
  const isEdit = !!job;

  const [form, setForm] = useState({
    title:       job?.title       || '',
    company:     job?.company     || '',
    location:    job?.location    || '',
    type:        job?.type        || 'Full-time',
    salary_min:  job?.salary_min  || '',
    salary_max:  job?.salary_max  || '',
    description: job?.description || '',
    requirements:job?.requirements|| '',
    skills:      job?.skills?.join(', ') || '',
  });
  const [errors, setErrors] = useState({});

  const set = (k) => (e) => { setForm((p) => ({ ...p, [k]: e.target.value })); setErrors((p) => ({ ...p, [k]: '' })); };

  const validate = () => {
    const e = {};
    if (!form.title.trim())    e.title    = 'Title is required';
    if (!form.description.trim()) e.description = 'Description is required';
    return e;
  };

  const handleSubmit = async (ev) => {
    ev.preventDefault();
    const e = validate();
    if (Object.keys(e).length) { setErrors(e); return; }

    const payload = {
      ...form,
      skills: form.skills.split(',').map((s) => s.trim()).filter(Boolean),
      salary_min: form.salary_min ? Number(form.salary_min) : null,
      salary_max: form.salary_max ? Number(form.salary_max) : null,
    };

    try {
      if (isEdit) await updateJob(job.id, payload);
      else        await createJob(payload);
      onSuccess?.();
    } catch {
      // Mutation hooks already surface errors to the user.
    }
  };

  const inputCls = (k) => `input ${errors[k] ? 'border-red-300 focus:ring-red-400' : ''}`;

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="label">Job Title *</label>
          <input type="text" placeholder="e.g. Senior React Developer" className={inputCls('title')} value={form.title} onChange={set('title')} />
          {errors.title && <p className="mt-1 text-xs text-red-500">{errors.title}</p>}
        </div>
        <div>
          <label className="label">Company</label>
          <input type="text" placeholder="Company name" className="input" value={form.company} onChange={set('company')} />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="label">Location</label>
          <input type="text" placeholder="e.g. Remote, New York" className="input" value={form.location} onChange={set('location')} />
        </div>
        <div>
          <label className="label">Job Type</label>
          <select className="input" value={form.type} onChange={set('type')}>
            {TYPES.map((t) => <option key={t}>{t}</option>)}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label className="label">Min Salary</label>
          <input type="number" placeholder="e.g. 60000" className="input" value={form.salary_min} onChange={set('salary_min')} />
        </div>
        <div>
          <label className="label">Max Salary</label>
          <input type="number" placeholder="e.g. 100000" className="input" value={form.salary_max} onChange={set('salary_max')} />
        </div>
      </div>

      <div>
        <label className="label">Required Skills</label>
        <input type="text" placeholder="React, TypeScript, Node.js (comma separated)" className="input" value={form.skills} onChange={set('skills')} />
      </div>

      <div>
        <label className="label">Job Description *</label>
        <textarea rows={5} placeholder="Describe the role, responsibilities…" className={`${inputCls('description')} resize-none`} value={form.description} onChange={set('description')} />
        {errors.description && <p className="mt-1 text-xs text-red-500">{errors.description}</p>}
      </div>

      <div>
        <label className="label">Requirements</label>
        <textarea rows={3} placeholder="Education, experience, certifications…" className="input resize-none" value={form.requirements} onChange={set('requirements')} />
      </div>

      <div className="flex justify-stretch gap-3 border-t border-gray-100 pt-2 sm:justify-end">
        <button type="submit" disabled={saving} className="btn-primary w-full justify-center px-6 sm:w-auto">
          {saving ? <Spinner size="sm" /> : isEdit ? 'Save Changes' : 'Post Job'}
        </button>
      </div>
    </form>
  );
};

export default JobForm;
