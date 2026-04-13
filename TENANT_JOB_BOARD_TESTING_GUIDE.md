# Tenant Job Board Testing Guide

This guide covers the strict tenant-isolation and resume-processing flow updated on `2026-04-10`.

## What Was Fixed

### 1. Strict tenant isolation
- Authenticated users are now locked to their own organization.
- Company A users cannot query Company B jobs, applicants, or candidate profiles.
- Public users can only see a company job board through that company slug.

### 2. Tenant routing context
- Middleware resolves:
  - requested organization slug
  - effective organization
  - job id
  - application id

### 3. Job and applicant data isolation
- `jobs/views.py` now scopes authenticated job access by organization.
- recruiter applicant access remains limited to recruiter-owned jobs in the same org.
- candidate profile/resume queries are organization-scoped.

### 4. Matching isolation
- resume-to-job matching is now organization-scoped.
- jobs from other organizations do not appear in matches.

### 5. Resume upload processing
- upload now performs an integrity checksum
- duplicate uploads return the existing resume
- upload returns quickly with `200` or `202`
- Celery-ready background task structure has been added
- local/sync mode stores locally first to avoid external storage dependency during parsing

### 6. Candidate application stage data
- application API returns:
  - `available_stages`
  - `current_stage`
  - `next_stage`
  - `next_update_at`
  - `status_label`
  - `is_terminal`

## Files Changed

### Backend
- `backend/ats_backend/core/middleware.py`
- `backend/ats_backend/authentication/organization.py`
- `backend/ats_backend/candidates/models.py`
- `backend/ats_backend/candidates/views.py`
- `backend/ats_backend/jobs/application_status.py`
- `backend/ats_backend/jobs/views.py`
- `backend/ats_backend/matching/utils.py`
- `backend/ats_backend/matching/views.py`
- `backend/ats_backend/resumes/views.py`
- `backend/ats_backend/resumes/processing.py`
- `backend/ats_backend/resumes/tasks.py`
- `backend/ats_backend/ats_backend/celery.py`
- `backend/ats_backend/jobs/tests.py`
- `backend/ats_backend/matching/tests.py`
- `backend/ats_backend/resumes/tests.py`

### Frontend
- `ats-frontend/src/components/candidate/ApplicationStatusCard.jsx`
- `ats-frontend/src/services/normalizers.js`

## Automated Testing

Run backend tests:

```powershell
cd C:\Users\lt22c\OneDrive\Desktop\ats_project\backend\ats_backend
..\.venv\Scripts\python.exe manage.py test --keepdb --noinput jobs.tests matching.tests resumes.tests --verbosity 1
```

Expected result:

```text
Ran 21 tests
OK
```

Run frontend build:

```powershell
cd C:\Users\lt22c\OneDrive\Desktop\ats_project\ats-frontend
npm run build
```

Expected result:

```text
vite build ... built successfully
```

## Local Run Setup

### Backend

```powershell
cd C:\Users\lt22c\OneDrive\Desktop\ats_project\backend\ats_backend
..\.venv\Scripts\python.exe manage.py runserver
```

### Frontend

```powershell
cd C:\Users\lt22c\OneDrive\Desktop\ats_project\ats-frontend
npm run dev
```

## Resume Processing Modes

### Local or sync mode
- `RESUME_PROCESSING_MODE=sync`
- upload returns `200`
- file is stored locally first
- parsing runs inside current process

### Async Celery mode
- `RESUME_PROCESSING_MODE=celery`
- configure `CELERY_BROKER_URL`
- upload returns `202`
- parsing is queued in the background

### Auto mode
- `RESUME_PROCESSING_MODE=auto`
- if broker exists, Celery is used
- if broker does not exist, sync/local mode is used

## Manual Test Cases

### Case 1: Public user can open a public org careers page
1. Open a public org route like `/careers/acme-hiring`
2. Verify jobs load
3. Open one job detail

Expected:
- public org jobs are visible
- job detail opens correctly

### Case 2: Public user cannot access private org board
1. Open `/jobs?organization_slug=private-org`
2. Or open a private job detail with that slug

Expected:
- API returns `404`
- frontend shows unavailable state

### Case 3: Authenticated candidate only sees own organization jobs
1. Login as candidate from Org A
2. Open `/jobs`

Expected:
- Org A jobs are visible
- Org B jobs are not visible even if Org B is public

### Case 4: Candidate cannot query another org by slug
1. Login as candidate from Org A
2. Open `/jobs?organization_slug=org-b`

Expected:
- API returns `404`

### Case 5: Candidate can only open same-org job detail
1. Login as candidate from Org A
2. Open job from Org A
3. Try direct URL for job from Org B

Expected:
- Org A job opens
- Org B job returns `404`

### Case 6: Recruiter remains tenant-scoped
1. Login as recruiter from Org A
2. Open recruiter jobs and applicants
3. Try accessing Org B job/applicant ids

Expected:
- only Org A data is visible
- Org B access is blocked

### Case 7: Candidate apply stays inside same tenant
1. Login as candidate from Org A
2. Apply to Org A job
3. Try applying to Org B job by direct id

Expected:
- Org A apply succeeds
- Org B apply is blocked

### Case 8: Candidate applications show stage info
1. Login as candidate
2. Open My Applications

Expected:
- card shows current stage
- card shows next stage or next update time
- progress line matches application status

### Case 9: Resume matches stay inside same org
1. Login as candidate with resume
2. Open matches page
3. Refresh matches

Expected:
- only same-org jobs appear
- cross-org jobs do not appear

### Case 10: Resume upload returns checksum and status
1. Login as candidate
2. Upload a valid PDF/DOCX

Expected:
- response is `200` or `202`
- response contains:
  - `resume_id`
  - `checksum_sha256`
  - `parsing_status`
  - `processing_mode`

### Case 11: Duplicate resume upload does not duplicate record
1. Upload the exact same file again

Expected:
- response is `200`
- message says resume already uploaded
- same `resume_id` is returned

## API Checks

### List jobs

```powershell
curl http://127.0.0.1:8000/api/jobs/
```

Expected:
- unauthenticated: only works in correct public org context
- authenticated: only current org jobs are returned

### Public org-specific jobs

```powershell
curl "http://127.0.0.1:8000/api/jobs/?organization_slug=acme-hiring"
```

Expected:
- only that org's jobs if board is public

### Candidate applications

```powershell
curl http://127.0.0.1:8000/api/jobs/applications/
```

Expected fields:
- `status`
- `status_label`
- `available_stages`
- `current_stage`
- `current_stage_index`
- `next_stage`
- `next_update_at`
- `is_terminal`

### Resume upload

```powershell
curl -X POST http://127.0.0.1:8000/api/resumes/upload/
```

Expected fields:
- `resume_id`
- `checksum_sha256`
- `parsing_status`
- `processing_mode`

## Recommended Test Data

Create 3 organizations:
- `default`
- `public-org`
- `private-org`

Settings:
- `public-org` => `allow_public_job_board=True`
- `private-org` => `allow_public_job_board=False`

Create:
- 1 candidate in `default`
- 1 recruiter in `default`
- 1 recruiter in `public-org`
- 1 recruiter in `private-org`
- 1 active job in `default`
- 2 active jobs in `public-org`
- 1 active job in `private-org`

## If Something Fails

### If backend tests stop because test DB already exists
Use:

```powershell
..\.venv\Scripts\python.exe manage.py test --keepdb --noinput jobs.tests matching.tests resumes.tests --verbosity 1
```

### If jobs still do not show
Check:
- user profile organization
- middleware is enabled in Django settings
- requested org slug is not from another tenant
- organization settings for public board

### If resume upload returns `400`
Check:
- file extension is `pdf` or `docx`
- file size is within limit
- file contents passed integrity validation

### If async queue does not run
Check:
- `RESUME_PROCESSING_MODE`
- `CELERY_BROKER_URL`
- worker process is running

## Final Verification Checklist

- Candidate only sees own org jobs
- Candidate cannot query another org jobs
- Recruiter only sees own org jobs and applicants
- Candidate/job matching stays tenant-scoped
- Resume upload returns checksum and status
- Duplicate resume upload reuses existing resume
- Application card shows live stage data
- Backend tests pass
- Frontend build passes
