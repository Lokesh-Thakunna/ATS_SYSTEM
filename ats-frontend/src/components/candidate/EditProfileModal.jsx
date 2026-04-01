import { useEffect, useMemo, useState } from 'react';
import Modal from '../ui/Modal';

const splitFullName = (fullName = '') => {
  const parts = fullName.trim().split(/\s+/).filter(Boolean);
  return {
    first_name: parts[0] || '',
    last_name: parts.slice(1).join(' '),
  };
};

const EditProfileModal = ({ open, profile, saving, onClose, onSave }) => {
  const initialForm = useMemo(() => {
    const { first_name, last_name } = splitFullName(profile?.full_name);
    return {
      first_name,
      last_name,
      email: profile?.email || '',
      phone: profile?.phone || '',
      summary: profile?.summary || '',
    };
  }, [profile]);

  const [form, setForm] = useState(initialForm);

  useEffect(() => {
    if (open) {
      setForm(initialForm);
    }
  }, [initialForm, open]);

  const setField = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }));

  const handleSubmit = async (event) => {
    event.preventDefault();
    await onSave?.({
      full_name: `${form.first_name} ${form.last_name}`.trim(),
      phone: form.phone,
      summary: form.summary,
    });
  };

  return (
    <Modal open={open} onClose={onClose} title="Edit Profile" size="md">
      <p className="mb-5 text-sm text-slate-500">Keep your profile up to date to improve your match rate.</p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="label">First Name</label>
            <input className="input" value={form.first_name} onChange={setField('first_name')} />
          </div>
          <div>
            <label className="label">Last Name</label>
            <input className="input" value={form.last_name} onChange={setField('last_name')} />
          </div>
        </div>

        <div>
          <label className="label">Email Address</label>
          <input className="input bg-slate-50" value={form.email} readOnly />
        </div>

        <div>
          <label className="label">Phone Number</label>
          <input className="input" value={form.phone} onChange={setField('phone')} />
        </div>

        <div>
          <label className="label">Professional Summary</label>
          <textarea
            rows={5}
            className="input resize-none"
            placeholder="Briefly describe your skills and experience..."
            value={form.summary}
            onChange={setField('summary')}
          />
        </div>

        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={saving} className="btn-primary flex-1 justify-center">
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
          <button type="button" onClick={onClose} className="btn-secondary flex-1 justify-center">
            Cancel
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default EditProfileModal;
