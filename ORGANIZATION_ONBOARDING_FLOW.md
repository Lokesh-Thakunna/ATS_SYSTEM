# Organization And Recruiter Onboarding Flow

## Recommended ownership model

1. Platform admin creates a new organization and its first organization admin.
2. Organization admin creates or invites recruiters inside that same organization.
3. Recruiter works only inside the assigned organization.
4. Recruiter can create jobs, review applicants, and move candidates through stages.
5. Recruiter cannot create a new organization.
6. Recruiter cannot create other recruiters unless you explicitly decide to loosen permissions later.

## Why this model is safer

- Tenant isolation stays clean because one recruiter always belongs to one organization.
- Organization creation remains a controlled action.
- Recruiter onboarding becomes predictable and auditable.
- Company A cannot accidentally create users inside Company B.

## Current backend rules

- `POST /api/auth/organizations/create/`
  - Allowed for platform admin only
  - Creates organization + first organization admin
- `POST /api/auth/recruiter/create/`
  - Allowed for organization admin
  - Creates recruiter inside admin's own organization only
- `POST /api/auth/organization/invites/`
  - Allowed for organization admin
  - Invite joins recruiter into admin's own organization only
- `POST /api/auth/register/recruiter/`
  - Disabled
  - Recruiters must join through organization admin flow

## Manual testing checklist

### 1. Platform admin creates organization

- Log in as platform admin
- Call `POST /api/auth/organizations/create/`
- Verify new organization is created
- Verify first org admin is created with role `admin`

### 2. Organization admin creates recruiter

- Log in as organization admin
- Open recruiter management page
- Create recruiter from the modal
- Verify recruiter appears in the same organization list
- Verify recruiter login works

### 3. Organization admin invites recruiter

- Log in as organization admin
- Create invite
- Open copied invite link
- Complete invite acceptance
- Verify created recruiter belongs to the same organization

### 4. Recruiter restrictions

- Log in as recruiter
- Try `POST /api/auth/recruiter/create/`
- Expect `403 Forbidden`
- Try `POST /api/auth/organizations/create/`
- Expect `403 Forbidden`

### 5. Public recruiter signup restriction

- Call `POST /api/auth/register/recruiter/`
- Expect `403 Forbidden`
- Verify no recruiter account and no new organization is created

## Suggested product wording

- `Platform admin` = creates organization and first org admin
- `Organization admin` = manages recruiters and organization settings
- `Recruiter` = manages jobs, applicants, kanban stages, interviews
- `Candidate` = applies, tracks status, uploads resume
