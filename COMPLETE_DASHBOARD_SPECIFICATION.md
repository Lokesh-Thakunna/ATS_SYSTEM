# ATS System - Complete Dashboard & Panel Specifications

**Date**: April 11, 2026  
**Version**: 1.0  
**Status**: Master Plan for All Panels

---

## 📑 Table of Contents

1. [Admin Dashboard (Super Admin)](#1-admin-dashboard-super-admin)
2. [Organization Management Panel](#2-organization-management-panel)
3. [Recruiter Dashboard](#3-recruiter-dashboard)
4. [Candidate Dashboard](#4-candidate-dashboard)
5. [Admin Settings Panel](#5-admin-settings-panel)
6. [Job Board Panel](#6-job-board-panel)
7. [Matches Panel](#7-matches-panel)
8. [Applications Management Panel](#8-applications-management-panel)
9. [Team Management Panel](#9-team-management-panel)
10. [Analytics & Reports Panel](#10-analytics--reports-panel)

---

## 📊 ROLE HIERARCHY

```
System Superadmin (Super Admin)
├── Platform admin (SUPER_ADMIN role)
│   ├── View all organizations
│   ├── Create new organizations
│   ├── Manage platform settings
│   └── View platform analytics
│
Organization Admin (ORG_ADMIN role)
├── Organization admins
│   ├── Manage team members
│   ├── Configure org settings
│   ├── View org analytics
│   └── Manage recruiters
│
Recruiters (RECRUITER role)
├── Recruiters
│   ├── Create & manage jobs
│   ├── Review applications
│   ├── Communicate with candidates
│   └── Track hiring progress
│
Candidates (CANDIDATE role)
└── Job seekers
    ├── Browse jobs
    ├── Apply for jobs
    ├── View applications
    └── Update resume/profile
```

---

## 1. ADMIN DASHBOARD (Super Admin)

**Route**: `/admin/dashboard`  
**Access**: SUPER_ADMIN role only  
**Purpose**: Platform-wide overview and management

### 📱 Panel Layout

#### Header Section
```
┌─────────────────────────────────────────────────────────┐
│  ATS Platform Admin Dashboard                 [Logout]  │
│  Welcome, [Admin Name]  | Last login: [Timestamp]       │
└─────────────────────────────────────────────────────────┘
```

#### Main Grid (3 columns)

**Column 1: Key Metrics Cards**
```
┌─────────────────────────┐
│ Platform Overview       │
├─────────────────────────┤
│ Total Organizations: 24 │
│ Active Users: 156       │
│ Total Jobs: 487         │
│ Applications: 2,341     │
│ Candidates: 892         │
│ Revenue: $48,500        │
└─────────────────────────┘
```

**Column 2: Top Organizations**
```
┌─────────────────────────────────────────────┐
│ Top Organizations (by activity)             │
├─────────────────────────────────────────────┤
│ 1. TechCorp Inc.        | 45 jobs, 234 apps│
│ 2. FinanceHub Ltd.      | 32 jobs, 189 apps│
│ 3. Design Studio        | 28 jobs, 156 apps│
│ 4. HR Solutions         | 19 jobs, 98 apps │
│ 5. MarketingPro         | 15 jobs, 67 apps │
│                                             │
│ [View All Organizations]                    │
└─────────────────────────────────────────────┘
```

**Column 3: System Health**
```
┌─────────────────────────┐
│ System Health Status    │
├─────────────────────────┤
│ ✓ API Status: Healthy   │
│ ✓ Database: Connected   │
│ ✓ Email: Operational    │
│ ✓ Cache: Running        │
│ ✓ Storage: 85% used     │
│ ✓ Uptime: 99.8%         │
│                         │
│ [Alert: High Load]      │
└─────────────────────────┘
```

#### Second Row: Analytics Charts

**Growth Chart**
```
Signups Trend (Last 30 days)
┌─────────────────────────────────────────┐
│     |                                   │
│     |*                                  │
│     | *                                 │
│     |  *                                │
│  R  |   **                              │
│  E  |     *                             │
│  A  |      *                            │
│  C  |       **                          │
│  H  |         *                         │
│     |          **                       │
│     |            *                      │
│     └─────────────────────────────────────│
       Day 1      Day 15      Day 30
```

**Applications Status (Pie Chart)**
```
┌────────────────────────────┐
│ Application Status         │
│                            │
│    ○─────○       Applied: 45%
│   ╱         ╲    In Review: 30%
│  │  45% 30% │   Interview: 18%
│  │    18%   │   Hired: 7%
│   ╲         ╱
│    ○─────○
└────────────────────────────┘
```

#### Third Row: Recent Activity & Quick Actions

**Recent Activity Log**
```
┌──────────────────────────────────────────────────┐
│ Recent Activity                                  │
├──────────────────────────────────────────────────┤
│ 10:45 - New org created: "AI Innovations"        │
│ 10:30 - Admin signup: john@techcorp.com          │
│ 10:15 - Job posted: "Senior ReactJS Dev"         │
│ 09:50 - Application submitted: John Doe          │
│ 09:30 - Email delivered: Org registration       │
│ 08:45 - Database backup completed successfully  │
└──────────────────────────────────────────────────┘
```

**Quick Actions Menu**
```
[+ Create Organization]  [+ Add Admin User]
[View Logs]              [System Settings]
[Email Queue]            [API Monitoring]
```

#### Footer: Advanced Controls

```
┌──────────────────────────────────────────────────┐
│ [Export Report]  [Advanced Search]  [Filters ▼] │
└──────────────────────────────────────────────────┘
```

### 📋 Components & Features

**Features**:
- Dashboard layout customization
- Real-time metrics updates (refresh every 5 sec)
- Email queue monitoring
- Error logs viewer
- System health alerts
- Bulk actions on organizations
- Generate platform reports
- API usage statistics
- User activity logs

**Data Displayed**:
- Total organizations count
- Active organizations
- Revenue metrics
- User statistics (by role)
- Job posting trends
- Application flow
- System performance
- Email delivery status

**Buttons & Actions**:
- Create new organization
- View organization details
- Manage admins
- Access logs
- Queue management
- System settings
- Export analytics
- Configure alerts

**Filters**:
- Date range (Last 7 days, 30 days, 90 days, custom)
- Organization type
- Status (active, inactive, suspended)
- Region/Country
- Industry

---

## 2. ORGANIZATION MANAGEMENT PANEL

**Route**: `/admin/organizations`  
**Access**: SUPER_ADMIN role only  
**Purpose**: Create, update, and manage organizations

### 📱 Panel Layout

#### Header
```
┌──────────────────────────────────────────────────────┐
│ Organization Management                 [+ Create]  │
│ Manage all organizations on the platform             │
└──────────────────────────────────────────────────────┘
```

#### Search & Filter Bar
```
┌─────────────────────────────────────────────────┐
│ 🔍 Search organizations                         │
│ [Filters]  [Sort By] [Export]  [Import]        │
└─────────────────────────────────────────────────┘
```

#### Organizations Table/List

**Table View**:
```
┌──────────────────────────────────────────────────────────────────┐
│ ☐ | Name          | Slug          | Status    | Users | Created │
├──────────────────────────────────────────────────────────────────┤
│ ☑ │ TechCorp Inc. │ techcorp-inc  │ Active    │ 12    │ Jan 15  │
│ ☐ │ FinanceHub    │ financehub    │ Active    │ 8     │ Feb 03  │
│ ☐ │ Design Co.    │ design-co     │ Inactive  │ 5     │ Mar 20  │
│ ☐ │ StartupAI     │ startup-ai    │ Active    │ 3     │ Apr 01  │
└──────────────────────────────────────────────────────────────────┘

Last column: [View] [Edit] [Delete] [More ...]
```

#### Action Modal: Create/Edit Organization

**Create Organization Form**:
```
┌─────────────────────────────────────────┐
│ Create New Organization                 │
├─────────────────────────────────────────┤
│                                         │
│ Organization Name *                    │
│ [_________________________________]    │
│                                         │
│ Slug (Auto-generate from name)         │
│ [_________________________________]    │
│                                         │
│ Admin Email *                          │
│ [_________________________________]    │
│                                         │
│ Website                                │
│ [_________________________________]    │
│                                         │
│ Industry                               │
│ [Select Industry ▼]                    │
│                                         │
│ Company Size                           │
│ ○ 1-10  ○ 11-50  ○ 51-200  ○ 200+    │
│                                         │
│ Description                            │
│ [________________________________]      │
│ [________________________________]      │
│                                         │
│ ☐ Send welcome email to admin          │
│                                         │
│   [Cancel]           [Create]          │
└─────────────────────────────────────────┘

After Create:
┌──────────────────────────────┐
│ ✓ Organization Created!      │
│                              │
│ Organization: TechCorp Inc.  │
│ Admin Email: admin@tc.com    │
│ Temp Password: Xr7#kL9@mQ2p │
│                              │
│ Email Status: Sent ✓         │
│                              │
│ Admin URL: /admin/...        │
│ [Copy Details] [View Org]    │
└──────────────────────────────┘
```

### 📋 Main Features

**Table Columns**:
- Organization name
- Slug/URL
- Status (active, inactive, suspended)
- User count
- Job count
- Application count
- Registration status
- Created date
- Last activity
- Actions (view, edit, delete, suspend)

**Actions Available**:
- Create new organization
- View organization details
- Edit organization info
- Suspend organization
- Soft delete organization
- Resend welcome email
- View organization admin
- View all users in org
- View statistics
- Export org data
- Bulk operations (select multiple)

**Information Displayed**:
- Organization details (name, slug, website, industry)
- Admin user info
- Registration tracking
- Email delivery status
- Team member count
- Job posting count
- Total applications
- Activity timeline

**Filters**:
- By status (active, inactive, suspended)
- By registration status (pending, completed, failed)
- By industry
- By date range
- By admin email
- By user count
- Search by name/slug

---

## 3. RECRUITER DASHBOARD

**Route**: `/recruiter/dashboard`  
**Access**: RECRUITER role only  
**Purpose**: Job posting and application management

### 📱 Panel Layout

#### Header Section
```
┌─────────────────────────────────────────────────┐
│ Recruiter Dashboard          Welcome, [Name]  │
│ [Organization Name]                [Logout]    │
└─────────────────────────────────────────────────┘
```

#### Quick Stats Cards (4 columns)

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Active Jobs  │  │ Applications │  │ In Interview │  │ Offers Sent  │
│      12      │  │      47      │  │       8      │  │      3       │
│ ↑ 2 new     │  │ ↓ 3 reviewed │  │ ↑ 5 new     │  │ = 1 accepted │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

#### Main Content Area (2 columns)

**Left Column: Job Management**
```
┌─────────────────────────────────────┐
│ My Jobs                 [+ New Job] │
├─────────────────────────────────────┤
│                                     │
│ 1. Senior React Developer           │
│    Posted: 5 days ago               │
│    Applications: 12                 │
│    Status: Active ✓                 │
│    [View] [Edit] [Close]           │
│                                     │
│ 2. UX/UI Designer                   │
│    Posted: 2 days ago               │
│    Applications: 8                  │
│    Status: Active ✓                 │
│    [View] [Edit] [Close]           │
│                                     │
│ 3. Project Manager                  │
│    Posted: 10 hours ago             │
│    Applications: 3                  │
│    Status: Active ✓                 │
│    [View] [Edit] [Close]           │
│                                     │
│ [View All Jobs]                     │
└─────────────────────────────────────┘
```

**Right Column: Recent Applications**
```
┌─────────────────────────────────────┐
│ Recent Applications                 │
├─────────────────────────────────────┤
│                                     │
│ John Doe - Senior React Dev         │
│ ⭐⭐⭐⭐⭐ (4.5/5)                 │
│ Status: [New]                       │
│ Applied: 2 hours ago                │
│ [View] [Quick Reject] [Interview]  │
│                                     │
│ Sarah Smith - React Developer       │
│ ⭐⭐⭐⭐ (4/5)                     │
│ Status: [In Review]                 │
│ Applied: 5 hours ago                │
│ [View] [Schedule Call] [Reject]    │
│                                     │
│ Mike Johnson - React Dev            │
│ ⭐⭐⭐⭐⭐ (4.5/5)                 │
│ Status: [Interview]                 │
│ Applied: 1 day ago                  │
│ [View] [Send Offer] [Reject]       │
│                                     │
│ [View All Applications]             │
└─────────────────────────────────────┘
```

#### Bottom Section: Activity & Matches

**Left: Pipeline Status**
```
┌────────────────────────────────────┐
│ Hiring Pipeline (This Month)       │
├────────────────────────────────────┤
│ Applied:        ████████ 47        │
│ Reviewed:       ██████ 32          │
│ Interview:      ██ 8               │
│ Offers:         █ 3                │
│ Hired:          1                  │
└────────────────────────────────────┘
```

**Right: Smart Matches**
```
┌──────────────────────────────────────┐
│ Matched Candidates                   │
│ (AI-powered recommendations)          │
├──────────────────────────────────────┤
│ ● Alex Wilson - 95% match             │
│   [React, Node, MongoDB]              │
│   [Invite to Apply]                   │
│                                      │
│ ● Emma Davis - 92% match              │
│   [React, TypeScript, AWS]            │
│   [Invite to Apply]                   │
│                                      │
│ ● David Lee - 88% match               │
│   [React, Vue, GraphQL]               │
│   [Invite to Apply]                   │
└──────────────────────────────────────┘
```

### 📋 Sub-Panels & Pages

#### A. Job Creation Panel
```
Route: /recruiter/jobs/create
┌─────────────────────────────────┐
│ Create New Job                  │
├─────────────────────────────────┤
│ Job Title *                     │
│ [Senior React Developer_________│
│                                 │
│ Job Type *                      │
│ ○ Full-time ○ Part-time ○ C2H  │
│                                 │
│ Location                        │
│ [Remote_________________________│
│                                 │
│ Description *                   │
│ [____________________...]        │
│                                 │
│ Required Skills *               │
│ [React] [Node] [MongoDB]        │
│ [Add Skill] [Remove Skill]      │
│                                 │
│ Salary Range                    │
│ $[80,000] - $[120,000]         │
│                                 │
│ Experience Required (years)     │
│ [3_________]                    │
│                                 │
│ [Cancel]  [Save Draft]  [Post] │
└─────────────────────────────────┘
```

#### B. Applications Management
```
Route: /recruiter/applications
Shows all applications with filters and bulk actions
- Filter by job, status, rating, date
- Sort by newest, rating, match score
- Bulk actions: schedule interview, send rejection, etc.
- Individual candidate evaluation
```

#### C. Candidate Profile Viewer
```
Route: /recruiter/candidates/:id
- Full candidate details
- Resume/CV download
- Communication history
- Application status tracker
- Interview scheduling
- Offer management
```

### 📋 Features

**Key Actions**:
- Create new job posting
- Edit/manage jobs
- Close job postings
- View full applications
- Screen candidates
- Schedule interviews
- Send offers
- Reject candidates
- Message candidates
- Download resumes
- Rate candidates

**Data Displayed**:
- Active jobs count and list
- Application statistics
- Candidate profiles with skills
- Communication history
- Interview notes
- Offer details
- Hiring pipeline status

---

## 4. CANDIDATE DASHBOARD

**Route**: `/candidate/dashboard`  
**Access**: CANDIDATE role only  
**Purpose**: Job search and application management

### 📱 Panel Layout

#### Header
```
┌────────────────────────────────────────────────┐
│ Job Seeker Dashboard          [Profile] [Logout]│
│ Hello, [Candidate Name]                        │
└────────────────────────────────────────────────┘
```

#### Main Content (3 sections)

**Section 1: Profile & Resume Status**
```
┌────────────────────────────┐
│ Your Profile               │
├────────────────────────────┤
│ [Profile Avatar]           │
│ [Name]                     │
│ [Email]                    │
│ [Phone]                    │
│ [Experience: 5 years]      │
│                            │
│ Resume Status: ✓ Active    │
│ [Upload Resume] [View as] │
│ Matches: 23                │
│                            │
│ [Edit Profile]             │
└────────────────────────────┘
```

**Section 2: Job Recommendations**
```
┌──────────────────────────────────────────────┐
│ Recommended Jobs (Based on Your Skills)      │
├──────────────────────────────────────────────┤
│                                              │
│ 1. Senior React Developer - TechCorp         │
│    Salary: $100k-$140k | Remote              │
│    Match: 95% ⭐⭐⭐⭐⭐              │
│    [Apply] [Save]                            │
│                                              │
│ 2. Frontend Engineer - StartupAI             │
│    Salary: $80k-$110k | Hybrid               │
│    Match: 92% ⭐⭐⭐⭐⭐              │
│    [Apply] [Save]                            │
│                                              │
│ 3. Full Stack Developer - FinanceHub         │
│    Salary: $90k-$130k | On-site              │
│    Match: 88% ⭐⭐⭐⭐              │
│    [Apply] [Save]                            │
│                                              │
│ [View All Jobs]                              │
└──────────────────────────────────────────────┘
```

**Section 3: Applications Status**
```
┌──────────────────────────────────────────────┐
│ My Applications                              │
├──────────────────────────────────────────────┤
│                                              │
│ Applied (3)      In Review (2)   Interview (1)
│ ┌──────────┐   ┌──────────┐   ┌──────────┐
│ │ Rejected │   │  Pending │   │ Scheduled│
│ │ Rejected │   │  Pending │   │ (Mar 15) │
│ │ Withdrawn│   │          │   │          │
│ └──────────┘   └──────────┘   └──────────┘
│
│ Completed: Senior React Dev       HIRED ✓
│
│ [View Details]
└──────────────────────────────────────────────┘
```

### 📋 Sub-Panels

#### A. Job Search/Browse
```
Route: /candidate/jobs
- Filterable job listing
- Search by keyword, location, salary
- Sort by newest, match score, salary
- Save jobs to favorites
- Apply directly
- View job details in modal
```

#### B. My Applications
```
Route: /candidate/applications
- Timeline view of all applications
- Status tracking (applied, reviewed, rejected, etc.)
- Communication with recruiters
- Interview scheduling
- Offer acceptance/decline
- Notes from candidates
```

#### C. Profile Management
```
Route: /candidate/profile
- Update basic information
- Edit experience
- Manage skills
- Upload resume/CV
- View profile as recruiters see it
- Privacy settings
```

#### D. Saved Jobs
```
Route: /candidate/saved
- List of bookmarked jobs
- Remove from saved
- Quick apply
- Email notifications for similar jobs
```

### 📋 Features

**Key Actions**:
- Browse and search jobs
- Apply for jobs
- Save jobs
- Track applications
- View interview details
- Accept/decline offers
- Update profile
- Upload resume
- Message recruiters
- Download offer letters
- Withdraw applications

---

## 5. ADMIN SETTINGS PANEL

**Route**: `/admin/settings`  
**Access**: ORG_ADMIN role only  
**Purpose**: Organization configuration

### 📱 Panel Layout

#### Sidebar Navigation
```
├─ Organization Settings
│  ├─ General
│  ├─ Branding
│  ├─ Email Templates
│  ├─ Automation
│  └─ API Keys
├─ Team Management
│  ├─ Members
│  ├─ Invitations
│  └─ Roles & Permissions
├─ Job Board
│  ├─ Public Page Settings
│  ├─ Career Site
│  └─ Publishing
└─ Analytics & Reports
   ├─ Hiring Metrics
   ├─ Export Data
   └─ Logs
```

#### Main Content: General Settings

**Form Cards**:

1. **Organization Details**
```
┌────────────────────────────────────┐
│ Organization Information           │
├────────────────────────────────────┤
│ Organization Name                  │
│ [TechCorp Inc.__________________]  │
│                                    │
│ Website                            │
│ [https://techcorp.com_____________│
│                                    │
│ Phone                              │
│ [+1-555-0100__________________₎  │
│                                    │
│ Industry                           │
│ [Select Industry ▼]                │
│                                    │
│ [Save Changes]                     │
└────────────────────────────────────┘
```

2. **Branding**
```
┌────────────────────────────────────┐
│ Branding & Logo                    │
├────────────────────────────────────┤
│ Logo                               │
│ [Upload Logo Image]                │
│ [Current Logo Preview]             │
│                                    │
│ Primary Color                      │
│ [Color Picker: #4f46e5]           │
│                                    │
│ Career Site Title                  │
│ [Awesome Careers at TechCorp_____] │
│                                    │
│ [Save Changes]                     │
└────────────────────────────────────┘
```

3. **Email Configuration**
```
┌────────────────────────────────────┐
│ Email Configuration                │
├────────────────────────────────────┤
│ From Email                         │
│ [careers@techcorp.com_____________│
│                                    │
│ SMTP Host                          │
│ [smtp.sendgrid.net________________│
│                                    │
│ SMTP Port                          │
│ [587___________________________]   │
│                                    │
│ ☐ Use TLS Encryption               │
│                                    │
│ [Test Email] [Save]                │
└────────────────────────────────────┘
```

### 📋 Sub-Sections Features

**Team Management**:
- Add/remove team members
- Assign roles (admin, recruiter, viewer)
- View pending invitations
- Resend invitation emails
- Remove members
- Activity logs

**Email Templates**:
- Customize welcome emails
- Application confirmation emails
- Rejection emails
- Interview scheduling templates
- Offer letter templates
- Custom templates

**Automation**:
- Auto-reject based on criteria
- Auto-schedule interviews
- Auto-send emails at specific stages
- Workflow rules

**Job Board Settings**:
- Enable/disable public job board
- Customize career page
- Publishing rules
- Job auto-archive settings

---

## 6. JOB BOARD PANEL

**Route**: `/jobs`  
**Access**: Authenticated users  
**Purpose**: Job listing and browsing

### 📱 Panel Layout

#### Header
```
┌────────────────────────────────────────┐
│ Job Board               [Search Box]   │
│ Browse & Apply to Jobs   [▼ Filters]  │
└────────────────────────────────────────┘
```

#### Content Layout (3 sections)

**Left Sidebar: Filters**
```
┌──────────────────────────┐
│ Filters                  │
├──────────────────────────┤
│ 🔍 Search Keywords       │
│ [_________________]      │
│                          │
│ 📍 Location              │
│ [Remote________▼]        │
│ ☐ Remote                 │
│ ☐ On-site                │
│ ☐ Hybrid                 │
│                          │
│ 💼 Job Type              │
│ ☐ Full-time              │
│ ☐ Part-time              │
│ ☐ Contract               │
│                          │
│ 💰 Salary Range          │
│ $[0]  ―  $[200k]        │
│                          │
│ 📚 Experience            │
│ [All Levels▼]            │
│                          │
│ 🏢 Company               │
│ [Select Company ▼]       │
│                          │
│ [Apply Filters]          │
└──────────────────────────┘
```

**Center: Job Listings**
```
┌─────────────────────────────────────────────┐
│ jobs found: 127 | Sort by: Newest ▼        │
├─────────────────────────────────────────────┤
│                                             │
│ Senior React Developer                      │
│ TechCorp Inc. • Remote • Full-time           │
│ $100k - $140k • 3-5 years experience        │
│ Skills: React, Node, MongoDB, AWS           │
│ ⭐ Matching Score: 95%                      │
│ Posted 2 days ago                           │
│ [View] [Apply]                              │
│                                             │
│ ─────────────────────────────────────────── │
│                                             │
│ Frontend Engineer                           │
│ StartupAI • San Francisco, CA • Full-time   │
│ $80k - $110k • 2-4 years experience         │
│ Skills: React, TypeScript, GraphQL          │
│ ⭐ Matching Score: 92%                      │
│ Posted 1 day ago                            │
│ [View] [Apply]                              │
│                                             │
│ ─────────────────────────────────────────── │
│                                             │
│ [Show More Results]                         │
└─────────────────────────────────────────────┘
```

**Right Sidebar: Job Details (when selected)**
```
┌──────────────────────────────────┐
│ Senior React Developer           │
├──────────────────────────────────┤
│ TechCorp Inc.                    │
│ Remote • Full-time               │
│ $100k - $140k                    │
│ 3-5 years experience             │
│                                  │
│ About the role                   │
│ We are looking for a...          │
│                                  │
│ Responsibilities                 │
│ • Develop web applications       │
│ • Lead frontend team             │
│ • Mentor junior developers       │
│                                  │
│ Required Skills                  │
│ • React (5+ years)               │
│ • Node.js                        │
│ • MongoDB                        │
│ • AWS                            │
│                                  │
│ Nice to have                     │
│ • TypeScript                     │
│ • GraphQL                        │
│ • Docker                         │
│                                  │
│ [Apply Now]  [Save]              │
└──────────────────────────────────┘
```

### 📋 Features

**Job Listing Features**:
- Search by keyword
- Filter by location, type, salary, experience
- Sort by newest, most relevant, salary
- Save jobs to bookmarks
- Apply directly
- View company profile
- Share job listings
- Pagination

**Job Detail Features**:
- Full job description
- Company information
- Skills matching
- Similar jobs recommendation
- Candidate reviews (if recruiter allows)
- Apply now button

---

## 7. MATCHES PANEL

**Route**: `/matches`  
**Access**: RECRUITER role  
**Purpose**: AI-powered candidate-job matching

### 📱 Panel Layout

#### Header
```
┌──────────────────────────────────────┐
│ AI Matches                           │
│ Smart candidate recommendations      │
└──────────────────────────────────────┘
```

#### Filters & Controls
```
[Show Matches For:] [Select Job ▼]  [Threshold: 80%+ ▼] [Sort by: Score ▼]
```

#### Matches Grid

**Candidate Card (3 columns)**
```
┌─────────────────────────┐
│ [Profile Pic]           │
│                         │
│ John Doe                │
│ Full Stack Developer    │
│ 5 years experience      │
│                         │
│ Skills: React, Node     │
│         MongoDB, AWS    │
│                         │
│ Match Score: 95%        │
│ ████████████████░░░     │
│                         │
│ 📄 Resume               │
│ 💬 Message              │
│ ➕ Invite to Apply      │
│                         │
│ [View Profile]          │
└─────────────────────────┘
```

**Match Reasons**:
```
Why this match?
✓ 5 years experience (Required: 3-5)
✓ Expert in React
✓ MongoDB experience
✓ AWS certified
✓ Available for remote work
✗ No GraphQL (nice to have)
```

### 📋 Features

**Matching Algorithm**:
- Skills matching
- Experience level matching
- Salary expectation alignment
- Location preference matching
- Availability matching
- Career growth matching

**Actions**:
- View full candidate profile
- Send direct message
- Invite to apply
- Schedule interview
- View matching reasons
- Export matches
- Bulk operations

---

## 8. APPLICATIONS MANAGEMENT PANEL

**Route**: `/recruiter/applications`  
**Access**: RECRUITER role  
**Purpose**: Track and manage all applications

### 📱 Panel Layout

#### Header with Stats
```
┌─────────────────────────────────────────────┐
│ Applications Management                     │
│ Total: 47 | New: 12 | In Review: 8 | Hired: 1
└─────────────────────────────────────────────┘
```

#### Pipeline View (Kanban-style)

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Applied  │  │ Reviewed │  │Interview │  │  Offer   │  │  Hired   │
│  [12]    │  │  [8]     │  │   [5]    │  │  [2]     │  │  [1]     │
├──────────┤  ├──────────┤  ├──────────┤  ├──────────┤  ├──────────┤
│          │  │          │  │          │  │          │  │          │
│ John Doe │  │Sarah Sm. │  │Mike John │  │Alex W.   │  │ Emma D.  │
│ React    │  │ ReactDev │  │ Full...  │  │ Senior..│  │ Hired ✓  │
│⭐⭐⭐⭐⭐      │⭐⭐⭐⭐      │⭐⭐⭐⭐⭐      │⭐⭐⭐⭐⭐      │ Start: May 1
│          │  │          │  │          │  │          │  │          │
│ Jane Doe │  │David Lee │  │          │  │ Sam P.   │  │          │
│ Frontend │  │ Full...  │  │          │  │ ReactDev │  │          │
│⭐⭐⭐⭐      │⭐⭐⭐      │          │  │⭐⭐⭐⭐⭐      │          │
│          │  │          │  │          │  │          │  │          │
│[Add]     │  │[Add]     │  │[Add]     │  │[Add]     │  │[Add]     │
└──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘

Drag & drop between stages
Click for details
```

#### Table View Alternative

```
┌─────────────────────────────────────────────────────┐
│ Candidate | Job | Status | Rating | Action | Notes  │
├─────────────────────────────────────────────────────┤
│ John Doe  │React Dev│New│⭐⭐⭐⭐⭐│[...]│Great fit│
│ Sarah Sm. │React Dev│Reviewing│⭐⭐⭐⭐│[...]│Good skills
│ Mike John │React Dev│Interview│⭐⭐⭐⭐⭐│[...]│Excellent│
│ Alex W.   │React Dev│Offered│⭐⭐⭐⭐⭐│[...]│Pending  │
│ Emma D.   │React Dev│Hired│⭐⭐⭐⭐⭐│[...]│Starts 1-May
└─────────────────────────────────────────────────────┘
```

### 📋 Features

**Application States**:
- New/Applied
- Under Review
- Interview Scheduled
- Interview Completed
- Offer Extended
- Offer Accepted
- Hired/Rejected
- Withdrawn

**Actions Per Application**:
- View full application
- Download resume
- Schedule interview
- Send message
- Send offer
- Reject
- Move to next stage
- Add notes
- Tag/bookmark

**Filters**:
- By status
- By job
- By date range
- By rating
- By recruiter
- Search by name

---

## 9. TEAM MANAGEMENT PANEL

**Route**: `/admin/team`  
**Access**: ORG_ADMIN role  
**Purpose**: Manage organization team members

### 📱 Panel Layout

#### Header
```
┌──────────────────────────────────────────┐
│ Team Management          [+ Invite Member]
│ Manage your recruitment team             │
└──────────────────────────────────────────┘
```

#### Members Table

```
┌──────────────────────────────────────────────────────┐
│ Name         │ Email              │ Role      │Action│
├──────────────────────────────────────────────────────┤
│ Admin        │ admin@techcorp.com │ Admin     │[Edit]
│ John Smith   │ john@techcorp.com  │ Recruiter │[Edit]
│ Sarah Jones  │ sarah@techcorp.com │ Recruiter │[Edit]
│ Mike Davis   │ mike@techcorp.com  │ Viewer    │[Edit]
└──────────────────────────────────────────────────────┘
```

#### Pending Invitations

```
┌──────────────────────────────────────────────┐
│ Pending Invitations                          │
├──────────────────────────────────────────────┤
│ alex@example.com - Recruiter Role            │
│ Invited: 2 days ago | Expires: in 5 days     │
│ [Resend] [Revoke]                            │
│                                              │
│ sam@example.com - Viewer Role                │
│ Invited: 5 hours ago | Expires: in 7 days    │
│ [Resend] [Revoke]                            │
└──────────────────────────────────────────────┘
```

#### Add New Member Modal

```
┌────────────────────────────────────────┐
│ Invite Team Member                     │
├────────────────────────────────────────┤
│ Email Address *                        │
│ [___________________________]          │
│                                        │
│ Role *                                 │
│ ○ Admin (Full Access)                  │
│ ○ Recruiter (Can post jobs & review)   │
│ ○ Viewer (View-only access)            │
│                                        │
│ Department (optional)                  │
│ [_________________________]            │
│                                        │
│ Permissions:                           │
│ ☑ Post & modify jobs                   │
│ ☑ View applications                    │
│ ☑ Schedule interviews                  │
│ ☑ Send offers                          │
│ ☐ Edit organization settings           │
│                                        │
│ [Cancel]  [Send Invite]                │
└────────────────────────────────────────┘
```

### 📋 Features

**Roles & Permissions**:
- Admin: Full access
- Recruiter: Post jobs, manage applications, schedule interviews
- Viewer: View-only access
- Custom roles with granular permissions

**Actions**:
- Invite new members
- Resend invitations
- Edit member roles
- Revoke invitations
- Remove members
- View member activity
- Set custom permissions

---

## 10. ANALYTICS & REPORTS PANEL

**Route**: `/admin/analytics`  
**Access**: ORG_ADMIN role  
**Purpose**: Hiring metrics and analytics

### 📱 Panel Layout

#### Date Range Selector
```
[Date Range: Last 30 Days ▼]  [Compare with: Previous Period]  [Export Report]
```

#### Key Metrics Cards

```
┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ Total Jobs     │ │ Applications   │ │ Avg Time to    │ │ Offer Accept   │
│ Posted: 12     │ │ Received: 284  │ │ Hire: 24 days  │ │ Rate: 87%      │
│ ↑ 25% vs prev  │ │ ↓ 12% vs prev  │ │ ↓ 3 days vs pr │ │ ↑ 5% vs prev   │
└────────────────┘ └────────────────┘ └────────────────┘ └────────────────┘
```

#### Main Charts (3 columns)

**Left: Applications Trend**
```
Applications Received (Last 30 days)
┌─────────────────────────────────┐
│     *                           │
│    / \                          │
│   /   *                         │
│  /     \                        │
│ /       *---*                   │
│              \                  │
│               *                 │
│                \---*            │
└─────────────────────────────────┘
```

**Center: Pipeline Breakdown**
```
Current Pipeline
┌────────────────────────────┐
│ Applied:     45%  ████████ │
│ Reviewing:   30%  ██████   │
│ Interviewing: 15% ███      │
│ Offered:      7%  █        │
│ Hired:        3%  █        │
└────────────────────────────┘
```

**Right: Time to Hire Distribution**
```
Time to Hire (Days)
┌────────────────────────────┐
│  5 days:     5 candidates  │
│ 10 days:    15 candidates  │
│ 15 days:    23 candidates  │
│ 20 days:    18 candidates  │
│ 25+ days:   12 candidates  │
│                            │
│ Average: 14.2 days         │
└────────────────────────────┘
```

#### Detailed Reports Section

```
┌─────────────────────────────────────────┐
│ Reports                                 │
├─────────────────────────────────────────┤
│                                         │
│ ▢ Job Performance Report                │
│   Analyze which jobs get most apps      │
│   [View] [Export]                       │
│                                         │
│ ▢ Source Analysis Report                │
│   Where candidates come from            │
│   [View] [Export]                       │
│                                         │
│ ▢ Hiring Funnel Report                  │
│   Application to hire conversion        │
│   [View] [Export]                       │
│                                         │
│ ▢ Recruiter Performance Report          │
│   Individual recruiter metrics          │
│   [View] [Export]                       │
│                                         │
│ ▢ Demographics Report                   │
│   Candidate demographics analysis       │
│   [View] [Export]                       │
│                                         │
│ ▢ Custom Report Builder                 │
│   Create custom reports                 │
│   [Build]                               │
└─────────────────────────────────────────┘
```

### 📋 Analytics Features

**Metrics Tracked**:
- Total applications
- Applications by source
- Time to hire
- Offer acceptance rate
- Candidate source effectiveness
- Job performance
- Recruiter performance
- Hiring funnel conversion
- Cost per hire
- Candidate quality metrics

**Reports Available**:
- Job performance
- Source analysis
- Hiring funnel
- Recruiter stats
- Demographic analysis
- Custom reports

**Export Options**:
- CSV export
- PDF reports
- Email scheduling
- Dashboard sharing

---

## 📱 RESPONSIVE DESIGN NOTES

All panels are designed to work on:
- **Desktop** (1920px+): Full 3-column layout
- **Tablet** (768px - 1024px): 2-column layout with collapsible sidebar
- **Mobile** (below 768px): Single column, stack sections vertically

---

## 🔒 SECURITY & PERMISSIONS

Each panel enforces role-based access control:
- Display elements only if user has permission
- API calls check authorization
- Sensitive data is encrypted
- Audit trails for sensitive actions
- Rate limiting on API endpoints

---

## 📊 DATA REFRESH STRATEGY

- Real-time updates: Application status changes, messages
- Periodic updates: Analytics (every 5 minutes)
- On-demand updates: Job listings, search results
- WebSocket for live notifications

---

## 🎨 DESIGN CONSISTENCY

All panels follow:
- Uniform color scheme
- Consistent typography
- Standard button styles
- Shared component library
- Mobile-first responsive design
- Accessibility guidelines (WCAG)

---

**Status**: ✅ **Complete Dashboard Specification**

All 10 major panels/dashboards are fully documented with:
- Layout specifications
- Feature descriptions
- Component details
- Data structures
- User flows
- Permissions

**Ready for Frontend Implementation**
