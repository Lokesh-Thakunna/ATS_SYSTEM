# ATS Backend API Documentation

## Base URL
```
http://localhost:8000/api
```

## Authentication Endpoints

### POST /api/auth/register/
Register a new user (candidate by default)

### POST /api/auth/register/recruiter/
Register a new recruiter

### POST /api/auth/login/
User login

### POST /api/auth/refresh/
Refresh JWT token

### POST /api/auth/logout/
User logout

## Organization Management

### GET /api/auth/organizations/
List all organizations

### POST /api/auth/organizations/create/
Create new organization

### DELETE /api/auth/organizations/{organization_id}/delete/
Delete organization

### GET /api/auth/recruiters/
List active recruiters

### POST /api/auth/recruiter/create/
Create new recruiter

### POST /api/auth/recruiter/deactivate/{user_id}/
Deactivate recruiter

## Job Management

### GET /api/jobs/
Get all jobs

### GET /api/jobs/recruiter/mine/
Get current recruiter's jobs

### GET /api/jobs/recruiter/applicants/
Get recruiter's applicants

### POST /api/jobs/create/
Create new job

### GET /api/jobs/{job_id}/
Get job details

### PUT /api/jobs/update/{job_id}/
Update job

### DELETE /api/jobs/delete/{job_id}/
Delete job

### POST /api/jobs/{job_id}/apply/
Apply for job

### GET /api/jobs/applications/
Get my applications

### PUT /api/jobs/applications/{application_id}/status/
Update application status

## Candidate Management

### GET /api/candidates/
Get all candidates

### GET /api/candidates/{candidate_id}/
Get candidate details

### PUT /api/candidates/{candidate_id}/
Update candidate profile

### POST /api/candidates/{candidate_id}/upload-resume/
Upload resume

### GET /api/candidates/{candidate_id}/download-resume/
Download resume

## Resume Processing

### POST /api/resumes/parse/
Parse resume text

### POST /api/resumes/extract-skills/
Extract skills from resume

### POST /api/resumes/analyze/
Analyze resume

### GET /api/resumes/text/{resume_id}/
Get resume text

### POST /api/resumes/upload-parse/
Upload and parse resume

### POST /api/resumes/validate/
Validate resume format

## Matching System

### POST /api/matching/calculate/
Calculate job-candidate match

### GET /api/matching/candidates/{job_id}/
Get matched candidates for job

### POST /api/matching/batch/
Batch calculate matches

### GET /api/matching/top/{job_id}/
Get top matches for job

### POST /api/matching/refresh/{job_id}/
Refresh job matches

### GET /api/matching/details/{match_id}/
Get match details

### PUT /api/matching/update/{match_id}/
Update match score

## Health Checks

### GET /health/
Basic health check

### GET /health/detailed/
Detailed health check with system metrics

## API Documentation

### GET /api/docs/
Interactive API documentation (HTML)

### GET /api/docs.json/
API documentation as JSON

## Error Responses

All endpoints return standard HTTP status codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

## Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Rate Limiting

API endpoints are rate-limited:
- Anonymous users: 100 requests/hour
- Authenticated users: 1000 requests/hour

## Pagination

List endpoints support pagination with `page` and `page_size` parameters.

---
*Last Updated: April 2026*
