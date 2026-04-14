import { useEffect, useState } from 'react';

import Button from '../ui/Button';
import Input from '../ui/Input';
import Modal from '../ui/Modal';
import Spinner from '../ui/Spinner';

const buildInitialState = (profile = {}) => ({
  full_name: profile.full_name || '',
  phone: profile.phone || '',
  summary: profile.summary || '',
});

const EditProfileModal = ({ open, profile, saving, onClose, onSave }) => {
  // Form state mirrors the editable candidate profile fields.
  const [form, setForm] = useState(buildInitialState(profile));

  // When the incoming profile changes, reset the form so the modal stays in sync.
  useEffect(() => {
    setForm(buildInitialState(profile));
  }, [profile]);

  const handleChange = (field) => (event) => {
    setForm((current) => ({ ...current, [field]: event.target.value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    await onSave?.(form);
  };

  return (
    <Modal open={open} onClose={onClose} title="Edit Candidate Profile" size="md">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Basic identity fields help the candidate keep their profile up to date. */}
        <div>
          <label className="label">Full Name</label>
          <Input value={form.full_name} onChange={handleChange('full_name')} placeholder="Your full name" required />
        </div>

        <div>
          <label className="label">Phone Number</label>
          <Input value={form.phone} onChange={handleChange('phone')} placeholder="+91 98765 43210" />
        </div>

        {/* Summary field gives the candidate a quick professional introduction. */}
        <div>
          <label className="label">Professional Summary</label>
          <textarea
            value={form.summary}
            onChange={handleChange('summary')}
            rows={5}
            className="input min-h-32 resize-y"
            placeholder="Write a short summary about your experience and strengths"
          />
        </div>

        {/* Footer actions keep save and close actions obvious. */}
        <div className="flex flex-col-reverse gap-3 sm:flex-row">
          <Button type="button" variant="outline" className="w-full justify-center" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" className="w-full justify-center" disabled={saving}>
            {saving ? <Spinner size="sm" /> : 'Save Changes'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default EditProfileModal;
