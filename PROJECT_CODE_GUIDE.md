# ATS Project Code Guide

This file explains:

1. how frontend and backend are connected
2. request-response flow
3. which file does what
4. where major logic lives
5. where I changed things to make the project work

The goal is simple: if you open this file and then open the code, you should quickly understand which part is doing what.

---

## 1. Project Structure

Root folders:

- `ats-frontend/`
  React + Vite frontend
- `backend/ats_backend/`
  Django + DRF backend

High-level architecture:

```text
Frontend UI
  -> services/*.js
  -> axios API client
  -> Django REST API
  -> models / views / serializers / matching / parsing
  -> PostgreSQL + pgvector + Supabase/local resume storage
```

---

## 2. How Frontend And Backend Are Connected

## 2.1 Main connection idea

Frontend never directly talks to the database.

Frontend flow:

1. user clicks something in UI
2. React page/component calls a service file
3. service file sends HTTP request to backend API
4. backend view processes request
5. backend reads/writes models
6. backend returns JSON response
7. frontend normalizes response and updates UI

---

## 2.2 Main frontend API layer

Main connection files:

- `ats-frontend/src/services/api.js`
  Central axios client. Base URL and auth token handling live here.

- `ats-frontend/src/services/authService.js`
  Connects login, register, recruiter admin actions with backend auth APIs.

- `ats-frontend/src/services/candidateService.js`
  Connects candidate profile and resume-related candidate APIs.

- `ats-frontend/src/services/jobsService.js`
  Connects jobs list, job detail, create/update/delete, apply flow, recruiter jobs, recruiter applicants.

- `ats-frontend/src/services/resumeService.js`
  Connects resume upload and matching APIs.

- `ats-frontend/src/services/normalizers.js`
  Converts backend JSON shape into stable frontend-friendly shape.

This is the real frontend-backend bridge.

---

## 2.3 Main backend API layer

Main backend API entry files:

- `backend/ats_backend/ats_backend/urls.py`
  Root router. It mounts all app APIs under `/api/...`.

- `backend/ats_backend/authentication/urls.py`
  Auth routes.

- `backend/ats_backend/candidates/urls.py`
  Candidate profile routes.

- `backend/ats_backend/jobs/urls.py`
  Job posting, applying, recruiter applicant routes.

- `backend/ats_backend/resumes/urls.py`
  Resume upload routes.

- `backend/ats_backend/matching/urls.py`
  Matching and ranking routes.

---

## 2.4 Exact connection map

### Auth

Frontend:

- `src/pages/auth/Login.jsx`
- `src/pages/auth/Register.jsx`
- `src/services/authService.js`
- `src/context/AuthContext.jsx`

Backend:

- `authentication/views.py`
- `authentication/services.py`
- `authentication/permissions.py`
- `authentication/models.py`

Flow:

```text
Login/Register page
  -> authService
  -> /api/auth/...
  -> authentication/views.py
  -> authentication/services.py
  -> User / UserProfile / Candidate / RecruiterProfile
  -> response returns tokens + user object
  -> AuthContext stores user and token
```

### Candidate Profile

Frontend:

- `src/pages/candidate/CandidateDashboard.jsx`
- `src/components/candidate/EditProfileModal.jsx`
- `src/services/candidateService.js`

Backend:

- `candidates/views.py`
- `candidates/models.py`

Flow:

```text
Candidate dashboard/edit modal
  -> candidateService.getProfile / updateProfile
  -> /api/candidates/profile...
  -> candidates/views.py
  -> Candidate model
  -> updated candidate JSON
```

### Jobs

Frontend:

- `src/pages/jobs/JobList.jsx`
- `src/pages/jobs/JobDetail.jsx`
- `src/pages/recruiter/RecruiterDashboard.jsx`
- `src/pages/recruiter/JobForm.jsx`
- `src/services/jobsService.js`

Backend:

- `jobs/views.py`
- `jobs/serializers.py`
- `jobs/models.py`

Flow:

```text
Job pages / recruiter dashboard
  -> jobsService
  -> /api/jobs/...
  -> jobs/views.py
  -> JobDescription / JobSkill / JobApplication
  -> serialized response
```

### Resume Upload + Parsing

Frontend:

- `src/pages/candidate/ResumePage.jsx`
- `src/services/resumeService.js`

Backend:

- `resumes/views.py`
- `resumes/serializers.py`
- `resumes/models.py`
- `services/parser/resume_parser.py`
- `services/parser/skills_extractor.py`
- `services/parser/experience_extractor.py`
- `services/parser/project_extractor.py`

Flow:

```text
Resume upload page
  -> resumeService.uploadResume
  -> /api/resumes/upload/
  -> resumes/views.py
  -> file validation
  -> Supabase/local upload
  -> parser extracts text/skills/experience/projects
  -> Resume + Skill + Project rows created
  -> matching recalculated
  -> frontend gets parsed result
```

### Matching

Frontend:

- `src/pages/candidate/MatchesPage.jsx`
- `src/pages/recruiter/RecruiterApplicantsPage.jsx`
- `src/services/resumeService.js`

Backend:

- `matching/views.py`
- `matching/utils.py`
- `matching/models.py`

Flow:

```text
Candidate matching page
  -> /api/matching/resume/:id/jobs/
  -> match jobs for candidate resume

Recruiter applicants page
  -> /api/matching/job/:id/applicants/
  -> rank only applied candidates for that recruiter's job
  -> recruiter can shortlist top N
```

---

## 3. Main Integration Work Done

These are the most important fixes that made frontend and backend work properly together:

### Auth contract aligned

- login now returns proper user payload
- register returns proper data
- superuser/staff treated as admin
- recruiter can log in by email / username / numeric ID

Main files:

- `authentication/views.py`
- `authentication/permissions.py`
- `authService.js`
- `Login.jsx`

### Candidate profile linked correctly

- candidate now has direct relation with `User`
- profile fetch/update no longer depends only on email matching
- old candidate rows were backfilled

Main files:

- `candidates/models.py`
- `candidates/views.py`
- `authentication/services.py`
- `candidates/migrations/0003_...py`

### Jobs and recruiter ownership fixed

- jobs now store `posted_by`
- recruiter sees only own jobs
- recruiter sees only applicants on own jobs
- legacy jobs were backfilled to correct recruiter

Main files:

- `jobs/models.py`
- `jobs/views.py`
- `jobs/serializers.py`
- `jobs/migrations/0005_...py`
- `jobs/migrations/0006_...py`

### Resume and matching flow aligned

- resume upload tied to authenticated candidate
- parsed resume data saved properly
- primary resume concept added
- storage metadata improved

Main files:

- `resumes/models.py`
- `resumes/views.py`
- `resumes/migrations/0005_...py`

### Matching engine upgraded

- scoring is now explainable and richer
- recruiter ranking is job-application-centric
- top N shortlist action added
- `shortlisted` is now real backend status

Main files:

- `matching/utils.py`
- `matching/views.py`
- `matching/tests.py`
- `jobs/models.py`
- `jobs/migrations/0008_alter_jobapplication_status.py`

---

## 4. Matching Logic Explained

This is the heart of the project.

Main file:

- `backend/ats_backend/matching/utils.py`

Now the score is not based on one single thing.

It uses a weighted hybrid score:

- skills match
- semantic similarity between job and candidate text
- experience fit
- title alignment
- education fit
- application quality / cover letter relevance
- penalties for critical gaps
- confidence based on available data quality

Why this is better:

- recruiter sees why a candidate got a score
- missing skills become visible
- only actual applicants are ranked for recruiter workflow
- top N shortlist becomes meaningful

Important backend recruiter matching routes:

- `GET /api/matching/job/<job_id>/applicants/`
  Ranks only applicants of that job

- `POST /api/matching/job/<job_id>/shortlist/`
  Shortlists top N candidates

---

## 5. Frontend File Explanations

Below is the frontend file-by-file explanation.

## 5.1 Root frontend files

### `ats-frontend/src/main.jsx`

Frontend entry point. React app starts here.

### `ats-frontend/src/App.jsx`

App wrapper. Usually holds top-level setup for routes/providers.

### `ats-frontend/src/App.css`

Basic app styling file. Less important than `index.css`.

### `ats-frontend/src/index.css`

Global styles. Current portal look, cards, buttons, panels, modal base styles come from here.

---

## 5.2 Assets

### `ats-frontend/src/assets/hero.png`

Image asset used in frontend visuals.

### `ats-frontend/src/assets/react.svg`

React default icon asset.

### `ats-frontend/src/assets/vite.svg`

Vite default icon asset.

---

## 5.3 Components

### Candidate components

#### `src/components/candidate/ApplicationStatusCard.jsx`

Reusable card for candidate application tracking.
Shows:

- job title
- timeline/status
- resume download
- reapply or shortlisted message

#### `src/components/candidate/EditProfileModal.jsx`

Modal used to edit candidate profile from dashboard.

### Shared components

#### `src/components/shared/Navbar.jsx`

Top navigation bar.
Shows current user, quick actions, sign out, etc.

#### `src/components/shared/Sidebar.jsx`

Left sidebar.
Different role-based navs:

- candidate
- recruiter
- admin

### UI components

#### `src/components/ui/Modal.jsx`

Reusable modal component.

#### `src/components/ui/Spinner.jsx`

Reusable loading spinner and page loader.

---

## 5.4 Context and hooks

### `src/context/AuthContext.jsx`

Central auth state.
Stores:

- current user
- token
- login/logout state
- updateUser helper

This is how user session is shared across all pages.

### `src/hooks/useAuth.js`

Small helper hook to consume auth context.

### `src/hooks/useJobs.js`

Custom hook for job fetching and job mutations.

---

## 5.5 Layouts

### `src/layouts/AppLayout.jsx`

Protected app layout with navbar + sidebar + content area.

### `src/layouts/AuthLayout.jsx`

Public layout for login/register pages.

---

## 5.6 Pages

### Generic page switcher

#### `src/pages/Dashboard.jsx`

Role-based dashboard router:

- candidate -> candidate dashboard
- recruiter -> recruiter dashboard
- admin -> admin dashboard

### Admin pages

#### `src/pages/admin/AdminDashboard.jsx`

Admin recruiter management page.
Shows active recruiters and deactivate actions.

### Auth pages

#### `src/pages/auth/Login.jsx`

Login UI.
Now supports:

- email
- username
- numeric login ID

#### `src/pages/auth/Register.jsx`

Registration UI.
Candidate/recruiter registration form logic starts here.

### Candidate pages

#### `src/pages/candidate/CandidateDashboard.jsx`

Main candidate portal dashboard.
Shows:

- profile summary
- profile strength
- stats
- recent applications
- edit profile modal flow

#### `src/pages/candidate/MatchesPage.jsx`

Shows candidate-job matches based on resume.
Uses matching API.

#### `src/pages/candidate/MyApplicationsPage.jsx`

Shows all applications with filters:

- all
- pending
- reviewing
- shortlisted
- rejected

#### `src/pages/candidate/ResumePage.jsx`

Resume upload and resume list page.

### Job pages

#### `src/pages/jobs/JobList.jsx`

Public/protected jobs listing page.

#### `src/pages/jobs/JobDetail.jsx`

Single job detail page.
Candidate applies from here.
Apply modal sends job application data to backend.

### Recruiter pages

#### `src/pages/recruiter/JobForm.jsx`

Create/update recruiter job form.

#### `src/pages/recruiter/RecruiterDashboard.jsx`

Recruiter job management dashboard.
Shows only recruiter's own jobs.

#### `src/pages/recruiter/RecruiterApplicantsPage.jsx`

Important recruiter page.
Now it shows:

- selected job
- top N input
- ranked applicants
- score breakdown
- strengths/gaps
- shortlist top N button

---

## 5.7 Routing

### `src/routes/AppRouter.jsx`

Main route map for the app.

### `src/routes/Guards.jsx`

Route protection:

- guest-only
- protected
- role-based

---

## 5.8 Services

### `src/services/api.js`

Central axios client.
Most important frontend infra file.

### `src/services/authService.js`

Auth API calls.

### `src/services/candidateService.js`

Candidate API calls.

### `src/services/jobsService.js`

Jobs API calls.
Used by:

- candidate job pages
- recruiter dashboard
- admin/recruiter actions

### `src/services/normalizers.js`

Normalizes backend response data into stable frontend objects.
Very useful because backend field names and frontend expectations can differ.

### `src/services/resumeService.js`

Resume upload + matching API calls.
Now includes recruiter applicant matching and shortlist API calls too.

---

## 5.9 Utilities

### `src/utils/helpers.js`

Formatting helpers like date, salary, job badge, time ago, etc.

---

## 6. Backend File Explanations

Below is the backend file-by-file explanation.

## 6.1 Django project core

### `backend/ats_backend/manage.py`

Django command runner.
Used for:

- server run
- migrations
- tests

### `backend/ats_backend/ats_backend/settings.py`

Global backend settings:

- installed apps
- DB config
- JWT
- CORS
- logging
- security settings

### `backend/ats_backend/ats_backend/urls.py`

Main API router.
Mounts all app URL files.

### `backend/ats_backend/ats_backend/asgi.py`

ASGI entry point.

### `backend/ats_backend/ats_backend/wsgi.py`

WSGI entry point.

### `backend/ats_backend/ats_backend/__init__.py`

Package initializer.

### `backend/ats_backend/ats_backend/utils/supabase_client.py`

Supabase client setup for file storage.

### `backend/ats_backend/ats_backend/utils/__init__.py`

Utility package initializer.

---

## 6.2 Authentication app

### `authentication/admin.py`

Django admin registration for auth app models.

### `authentication/apps.py`

App config.

### `authentication/models.py`

Stores:

- `UserProfile`
  role mapping for each user
- `RecruiterProfile`
  recruiter company info
- `AuditLog`
  admin/recruiter audit entries

### `authentication/permissions.py`

Role-based permission classes.
Important because this decides:

- admin access
- recruiter access
- candidate access

### `authentication/serializers.py`

Serializer file for auth app. Less central than views/services here.

### `authentication/services.py`

Business logic for:

- create candidate
- create recruiter
- deactivate recruiter

Good file when you want to see creation logic without API noise.

### `authentication/tests.py`

Tests for registration/auth behavior.

### `authentication/urls.py`

Auth routes.

### `authentication/views.py`

Main auth APIs:

- register candidate
- register recruiter
- login
- admin recruiter listing
- recruiter deactivate

This is one of the most important backend files.

### `authentication/migrations/0001_initial.py`

Initial auth app DB schema.

### `authentication/migrations/0002_alter_auditlog_options_and_more.py`

Later production hardening migration:

- indexes
- timestamps
- ordering
- better fields

---

## 6.3 Candidates app

### `candidates/admin.py`

Admin integration.

### `candidates/apps.py`

App config.

### `candidates/models.py`

Main candidate profile table.
Stores:

- linked auth user
- full name
- email
- phone
- summary
- total experience
- resume URL/file name

### `candidates/tests.py`

Candidate app tests if present/expanded later.

### `candidates/urls.py`

Candidate routes.

### `candidates/views.py`

APIs for:

- get candidate profile
- update candidate profile
- create/update candidate profile
- get candidate resumes

### `candidates/migrations/0001_initial.py`

Initial candidate table.

### `candidates/migrations/0002_candidate_resume_fields.py`

Added resume tracking fields to candidate.

### `candidates/migrations/0003_alter_candidate_options_candidate_user_and_more.py`

Important migration:

- linked candidate to Django user
- added indexes/constraints
- backfilled legacy data

---

## 6.4 Core app

### `core/api_docs.py`

Optional API docs helper.

### `core/exceptions.py`

Custom application exceptions.

### `core/exception_handlers.py`

Global exception response formatter.

### `core/health_checks.py`

Health check endpoints.

### `core/logger.py`

Central logger helper.

### `core/middleware.py`

Custom middleware, mainly security/logging.

### `core/validators.py`

Very important validation layer.
Checks:

- email
- password
- full name
- phone
- resume file
- salary
- experience

### `core/management/commands/clean_embeddings.py`

Management command for embedding cleanup.

### `core/management/commands/generate_job_embeddings.py`

Batch command to generate job embeddings.

### `core/management/commands/generate_resume_embeddings.py`

Batch command to generate resume embeddings.

---

## 6.5 Jobs app

### `jobs/admin.py`

Admin registration.

### `jobs/apps.py`

App config.

### `jobs/models.py`

Core recruitment data model:

- `JobDescription`
- `JobSkill`
- `JobApplication`

Important fields:

- `posted_by`
- job title/desc/requirements
- salary
- experience
- applicant status
- shortlisted support

### `jobs/serializers.py`

Shapes job data for API responses.
Maps backend model shape to clean JSON.

### `jobs/tests.py`

Jobs app tests.

### `jobs/urls.py`

Routes for:

- list jobs
- recruiter own jobs
- recruiter own applicants
- create/update/delete jobs
- apply for job
- get my applications

### `jobs/views.py`

One of the most important backend files.

Contains:

- create job
- get jobs
- get recruiter jobs
- update/delete owned job
- recruiter applicant listing
- apply for job
- get my applications

This file is where most recruiter-candidate operational flow happens.

### `jobs/utils/embedding.py`

Sentence-transformer embedding generator for job text.

### `jobs/migrations/0001_initial.py`

Initial job tables.

### `jobs/migrations/0002_alter_jobdescription_embedding.py`

Migrated job embedding to pgvector.
Now also ensures vector extension is available.

### `jobs/migrations/0003_jobdescription_company_job_type_requirements.py`

Added more job fields needed by frontend.

### `jobs/migrations/0004_alter_jobdescription_created_at.py`

Adjusted created_at behavior.

### `jobs/migrations/0005_jobdescription_posted_by.py`

Added recruiter ownership to jobs.

### `jobs/migrations/0006_backfill_posted_by_for_existing_jobs.py`

Backfilled old jobs to correct recruiter.

### `jobs/migrations/0007_alter_jobapplication_options_and_more.py`

Production-hardening migration:

- indexes
- constraints
- ordering
- application consistency

### `jobs/migrations/0008_alter_jobapplication_status.py`

Added formal `shortlisted` status.

---

## 6.6 Matching app

### `matching/admin.py`

Admin registration for matching tables.

### `matching/apps.py`

App config.

### `matching/models.py`

Stores:

- `MatchScore`
- `AIProcessingLog`

These are persistent scoring/logging tables.

### `matching/tests.py`

Matching engine and recruiter applicant ranking tests.

### `matching/urls.py`

Matching endpoints.

### `matching/utils.py`

Most important matching logic file.

Contains:

- cosine similarity
- text normalization
- skill alias matching
- experience fit logic
- title alignment logic
- education fit logic
- application/cover letter relevance
- confidence score
- final hybrid score
- recruiter applicant ranking

If you want to understand how candidate ranking works, start here.

### `matching/views.py`

API layer for matching.
Contains:

- match jobs for resume
- match jobs for candidate
- match candidates for job
- match applicants for recruiter job
- shortlist top candidates
- match one resume to one job

### `matching/migrations/0001_initial.py`

Formalized existing matching tables into migration graph.

### `matching/migrations/0002_alter_aiprocessinglog_options_and_more.py`

Added constraints/indexes/options to matching tables.

---

## 6.7 Resumes app

### `resumes/admin.py`

Admin integration.

### `resumes/apps.py`

App config.

### `resumes/models.py`

Resume system tables:

- `Resume`
- `Skill`
- `Education`
- `Experience`
- `Project`

Important concepts:

- primary active resume
- storage backend
- parsing status
- file metadata

### `resumes/serializers.py`

Resume upload serializer.

### `resumes/tests.py`

Resume tests.

### `resumes/urls.py`

Resume API routes.

### `resumes/views.py`

Handles:

- upload resume
- parse resume
- save extracted data
- trigger matching recalculation

### `resumes/migrations/0001_initial.py`

Initial resume tables.

### `resumes/migrations/0002_resume_embedding.py`

Added pgvector resume embedding and vector extension support.

### `resumes/migrations/0003_experience_project.py`

Added project and experience related tables.

### `resumes/migrations/0004_alter_experience_id_alter_project_id.py`

Adjusted keys/IDs.

### `resumes/migrations/0005_alter_education_options_alter_resume_options_and_more.py`

Important production-hardening migration:

- primary resume
- storage metadata
- constraints
- indexes
- backfill logic

---

## 6.8 Resume parser service

### `services/parser/admin.py`

Admin integration.

### `services/parser/apps.py`

App config.

### `services/parser/experience_extractor.py`

Extracts experience info from resume text.

### `services/parser/models.py`

Currently minimal placeholder model file.

### `services/parser/project_extractor.py`

Extracts project names/data from resume text.

### `services/parser/resume_parser.py`

Main parsing orchestrator.
Reads file text and calls extractors.

### `services/parser/skills_extractor.py`

Extracts skills from parsed text.

### `services/parser/tests.py`

Parser tests.

### `services/parser/urls.py`

Parser-related endpoints.

### `services/parser/views.py`

Parser API views.

---

## 6.9 Project tests

### `backend/ats_backend/tests/test_api_endpoints.py`

High-level API endpoint tests across multiple modules.

---

## 7. Where To Start If You Want To Understand The Code Fast

If you want fastest understanding, open files in this order:

### Frontend order

1. `ats-frontend/src/routes/AppRouter.jsx`
2. `ats-frontend/src/context/AuthContext.jsx`
3. `ats-frontend/src/services/api.js`
4. `ats-frontend/src/services/authService.js`
5. `ats-frontend/src/services/jobsService.js`
6. `ats-frontend/src/services/resumeService.js`
7. `ats-frontend/src/pages/Dashboard.jsx`
8. role-specific pages:
   - `candidate/CandidateDashboard.jsx`
   - `recruiter/RecruiterDashboard.jsx`
   - `recruiter/RecruiterApplicantsPage.jsx`
   - `admin/AdminDashboard.jsx`
9. `pages/jobs/JobDetail.jsx`

### Backend order

1. `backend/ats_backend/ats_backend/urls.py`
2. `backend/ats_backend/ats_backend/settings.py`
3. `backend/ats_backend/authentication/views.py`
4. `backend/ats_backend/authentication/services.py`
5. `backend/ats_backend/candidates/models.py`
6. `backend/ats_backend/candidates/views.py`
7. `backend/ats_backend/jobs/models.py`
8. `backend/ats_backend/jobs/views.py`
9. `backend/ats_backend/resumes/views.py`
10. `backend/ats_backend/resumes/models.py`
11. `backend/ats_backend/matching/views.py`
12. `backend/ats_backend/matching/utils.py`

---

## 8. Best Mental Model For This Project

Think of the system in 5 layers:

### Layer 1: Auth + roles

Who is the user?

- admin
- recruiter
- candidate

### Layer 2: Candidate and recruiter business data

What extra data belongs to that user?

- candidate profile
- recruiter company profile

### Layer 3: Jobs and applications

Which recruiter posted which job?
Which candidate applied where?

### Layer 4: Resume intelligence

What is inside the candidate resume?

- skills
- projects
- experience
- education

### Layer 5: Matching and ranking

Given job + candidate application + resume, how good is the fit?

This final layer powers:

- candidate job recommendations
- recruiter applicant ranking
- top N shortlist

---

## 9. Short Summary

If you remember only this:

- frontend talks to backend only through `services/*.js`
- backend routes start in `ats_backend/urls.py`
- most business logic is in `authentication/services.py`, `jobs/views.py`, `resumes/views.py`, `matching/utils.py`
- recruiter ownership is controlled by `posted_by`
- candidate identity is now linked with `Candidate.user`
- matching heart is `matching/utils.py`
- recruiter ranking page is `src/pages/recruiter/RecruiterApplicantsPage.jsx`

---

## 10. File Created For Understanding

This guide file itself is intentionally outside both frontend and backend:

- `PROJECT_CODE_GUIDE.md`

So whenever you feel confused, open this file first, then jump to the exact code file mentioned here.
