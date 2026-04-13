-- Multi-Tenant ATS Database Schema
-- Complete schema with organization_id isolation for data privacy

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- =====================================
-- CORE TENANT STRUCTURE
-- =====================================

-- Organizations (Tenants)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    website VARCHAR(500),
    industry VARCHAR(100),
    company_size VARCHAR(50) CHECK (company_size IN ('1-10', '11-50', '51-200', '200+', '1000+')),
    description TEXT,
    logo_url VARCHAR(500),
    primary_color VARCHAR(7) DEFAULT '#4f46e5',
    secondary_color VARCHAR(7) DEFAULT '#64748b',
    settings JSONB DEFAULT '{}',
    subscription_plan VARCHAR(50) DEFAULT 'basic',
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for organization lookup
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_status ON organizations(status);

-- =====================================
-- USER MANAGEMENT WITH ROLES
-- =====================================

-- Users with Role-Based Access Control
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    role VARCHAR(20) NOT NULL CHECK (role IN ('SUPER_ADMIN', 'ORG_ADMIN', 'RECRUITER', 'CANDIDATE')),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true,
    is_email_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMP WITH TIME ZONE,
    profile_picture_url VARCHAR(500),
    bio TEXT,
    location VARCHAR(255),
    linkedin_url VARCHAR(500),
    github_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for user queries
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_organization_id ON users(organization_id);
CREATE INDEX idx_users_is_active ON users(is_active);

-- =====================================
-- JOB MANAGEMENT (TENANT-SCOPED)
-- =====================================

-- Job Postings
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    requirements TEXT,
    responsibilities TEXT,
    benefits TEXT,
    job_type VARCHAR(50) NOT NULL CHECK (job_type IN ('full-time', 'part-time', 'contract', 'internship', 'temporary')),
    work_mode VARCHAR(50) DEFAULT 'office' CHECK (work_mode IN ('office', 'remote', 'hybrid')),
    location VARCHAR(255),
    salary_min DECIMAL(10,2),
    salary_max DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    experience_required INTEGER CHECK (experience_required >= 0),
    education_level VARCHAR(100),
    required_skills TEXT[],
    preferred_skills TEXT[],
    department VARCHAR(100),
    report_to VARCHAR(255),
    vacancy_count INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'closed', 'archived')),
    is_featured BOOLEAN DEFAULT false,
    posted_by UUID REFERENCES users(id) ON DELETE SET NULL,
    published_at TIMESTAMP WITH TIME ZONE,
    closes_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, slug)
);

-- Create indexes for job queries
CREATE INDEX idx_jobs_organization_id ON jobs(organization_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_job_type ON jobs(job_type);
CREATE INDEX idx_jobs_work_mode ON jobs(work_mode);
CREATE INDEX idx_jobs_posted_by ON jobs(posted_by);
CREATE INDEX idx_jobs_published_at ON jobs(published_at);
CREATE INDEX idx_jobs_skills_gin ON jobs USING GIN(required_skills);

-- =====================================
-- CANDIDATE MANAGEMENT
-- =====================================

-- Candidate Profiles (Extended from users table)
CREATE TABLE candidate_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    headline VARCHAR(255),
    summary TEXT,
    experience_years INTEGER,
    current_title VARCHAR(255),
    current_company VARCHAR(255),
    resume_url VARCHAR(500),
    resume_file_name VARCHAR(255),
    resume_text_content TEXT,
    skills TEXT[],
    education JSONB DEFAULT '[]',
    experience JSONB DEFAULT '[]',
    certifications JSONB DEFAULT '[]',
    portfolio_url VARCHAR(500),
    salary_expectation_min DECIMAL(10,2),
    salary_expectation_max DECIMAL(10,2),
    preferred_locations TEXT[],
    job_types TEXT[],
    work_modes TEXT[],
    is_active BOOLEAN DEFAULT true,
    is_visible_to_recruiters BOOLEAN DEFAULT true,
    linkedin_profile_url VARCHAR(500),
    github_profile_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, organization_id)
);

-- Create indexes for candidate profiles
CREATE INDEX idx_candidate_profiles_user_id ON candidate_profiles(user_id);
CREATE INDEX idx_candidate_profiles_organization_id ON candidate_profiles(organization_id);
CREATE INDEX idx_candidate_profiles_skills_gin ON candidate_profiles USING GIN(skills);
CREATE INDEX idx_candidate_profiles_experience_years ON candidate_profiles(experience_years);

-- =====================================
-- APPLICATION MANAGEMENT
-- =====================================

-- Job Applications
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    candidate_id UUID REFERENCES users(id) ON DELETE CASCADE,
    candidate_profile_id UUID REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    resume_url VARCHAR(500),
    cover_letter TEXT,
    status VARCHAR(20) DEFAULT 'applied' CHECK (status IN ('applied', 'reviewing', 'screening', 'interview', 'offer', 'rejected', 'withdrawn', 'hired')),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    match_score DECIMAL(5,2) CHECK (match_score >= 0 AND match_score <= 100),
    notes TEXT,
    internal_notes TEXT,
    source VARCHAR(100),
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(job_id, candidate_id)
);

-- Create indexes for applications
CREATE INDEX idx_applications_organization_id ON applications(organization_id);
CREATE INDEX idx_applications_job_id ON applications(job_id);
CREATE INDEX idx_applications_candidate_id ON applications(candidate_id);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_rating ON applications(rating);
CREATE INDEX idx_applications_match_score ON applications(match_score);
CREATE INDEX idx_applications_applied_at ON applications(applied_at);

-- =====================================
-- INTERVIEW MANAGEMENT
-- =====================================

-- Interview Schedules
CREATE TABLE interviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    candidate_id UUID REFERENCES users(id) ON DELETE CASCADE,
    interviewer_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    interview_type VARCHAR(50) CHECK (interview_type IN ('phone', 'video', 'onsite', 'technical', 'behavioral')),
    duration_minutes INTEGER DEFAULT 60,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    location VARCHAR(255),
    meeting_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled', 'rescheduled')),
    feedback TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for interviews
CREATE INDEX idx_interviews_organization_id ON interviews(organization_id);
CREATE INDEX idx_interviews_application_id ON interviews(application_id);
CREATE INDEX idx_interviews_candidate_id ON interviews(candidate_id);
CREATE INDEX idx_interviews_interviewer_id ON interviews(interviewer_id);
CREATE INDEX idx_interviews_scheduled_at ON interviews(scheduled_at);
CREATE INDEX idx_interviews_status ON interviews(status);

-- =====================================
-- OFFER MANAGEMENT
-- =====================================

-- Job Offers
CREATE TABLE offers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    candidate_id UUID REFERENCES users(id) ON DELETE CASCADE,
    offer_title VARCHAR(255) NOT NULL,
    salary_amount DECIMAL(10,2),
    salary_currency VARCHAR(3) DEFAULT 'USD',
    bonus_amount DECIMAL(10,2),
    start_date DATE,
    benefits TEXT,
    terms_conditions TEXT,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'accepted', 'declined', 'expired', 'withdrawn')),
    sent_at TIMESTAMP WITH TIME ZONE,
    responded_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for offers
CREATE INDEX idx_offers_organization_id ON offers(organization_id);
CREATE INDEX idx_offers_application_id ON offers(application_id);
CREATE INDEX idx_offers_candidate_id ON offers(candidate_id);
CREATE INDEX idx_offers_status ON offers(status);
CREATE INDEX idx_offers_sent_at ON offers(sent_at);

-- =====================================
-- TEAM MANAGEMENT
-- =====================================

-- Team Invitations
CREATE TABLE team_invitations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('ORG_ADMIN', 'RECRUITER')),
    invited_by UUID REFERENCES users(id) ON DELETE SET NULL,
    invitation_token VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'expired')),
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accepted_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '7 days'),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for team invitations
CREATE INDEX idx_team_invitations_organization_id ON team_invitations(organization_id);
CREATE INDEX idx_team_invitations_email ON team_invitations(email);
CREATE INDEX idx_team_invitations_token ON team_invitations(invitation_token);
CREATE INDEX idx_team_invitations_status ON team_invitations(status);

-- =====================================
-- ACTIVITY LOGS
-- =====================================

-- Activity Logs (Audit Trail)
CREATE TABLE activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for activity logs
CREATE INDEX idx_activity_logs_organization_id ON activity_logs(organization_id);
CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX idx_activity_logs_action ON activity_logs(action);
CREATE INDEX idx_activity_logs_resource_type ON activity_logs(resource_type);
CREATE INDEX idx_activity_logs_created_at ON activity_logs(created_at);

-- =====================================
-- SYSTEM CONFIGURATION
-- =====================================

-- System Settings (Platform-wide)
CREATE TABLE system_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Email Templates
CREATE TABLE email_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    html_content TEXT NOT NULL,
    text_content TEXT,
    variables JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, name)
);

-- Create indexes for email templates
CREATE INDEX idx_email_templates_organization_id ON email_templates(organization_id);
CREATE INDEX idx_email_templates_name ON email_templates(name);

-- =====================================
-- AI MATCHING & SEARCH
-- =====================================

-- Job Embeddings (for AI matching)
CREATE TABLE job_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(job_id)
);

-- Candidate Embeddings (for AI matching)
CREATE TABLE candidate_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_profile_id UUID REFERENCES candidate_profiles(id) ON DELETE CASCADE,
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(candidate_profile_id)
);

-- Create indexes for embeddings
CREATE INDEX idx_job_embeddings_job_id ON job_embeddings(job_id);
CREATE INDEX idx_candidate_embeddings_candidate_profile_id ON candidate_embeddings(candidate_profile_id);

-- =====================================
-- TRIGGERS & FUNCTIONS
-- =====================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_candidate_profiles_updated_at BEFORE UPDATE ON candidate_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_applications_updated_at BEFORE UPDATE ON applications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_interviews_updated_at BEFORE UPDATE ON interviews FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_offers_updated_at BEFORE UPDATE ON offers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_team_invitations_updated_at BEFORE UPDATE ON team_invitations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_email_templates_updated_at BEFORE UPDATE ON email_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================
-- VIEWS FOR COMMON QUERIES
-- =====================================

-- View for active jobs with organization info
CREATE VIEW active_jobs_view AS
SELECT 
    j.*,
    o.name as organization_name,
    o.logo_url as organization_logo,
    o.primary_color as organization_color
FROM jobs j
JOIN organizations o ON j.organization_id = o.id
WHERE j.status = 'active' AND j.published_at <= NOW();

-- View for application statistics
CREATE VIEW application_stats_view AS
SELECT 
    o.id as organization_id,
    o.name as organization_name,
    COUNT(DISTINCT j.id) as total_jobs,
    COUNT(DISTINCT a.id) as total_applications,
    COUNT(DISTINCT CASE WHEN a.status = 'applied' THEN a.id END) as applied_count,
    COUNT(DISTINCT CASE WHEN a.status = 'interview' THEN a.id END) as interview_count,
    COUNT(DISTINCT CASE WHEN a.status = 'offer' THEN a.id END) as offer_count,
    COUNT(DISTINCT CASE WHEN a.status = 'hired' THEN a.id END) as hired_count
FROM organizations o
LEFT JOIN jobs j ON o.id = j.organization_id AND j.status = 'active'
LEFT JOIN applications a ON j.id = a.job_id
GROUP BY o.id, o.name;

-- =====================================
-- SAMPLE DATA (for development)
-- =====================================

-- Insert sample system settings
INSERT INTO system_settings (key, value, description, is_public) VALUES
('platform_name', 'ATS Platform', 'Name of the platform', true),
('default_currency', 'USD', 'Default currency for salaries', true),
('max_file_size_mb', '10', 'Maximum file size for uploads in MB', false),
('email_from_address', 'noreply@atsplatform.com', 'Default from email address', false);

-- =====================================
-- SECURITY POLICIES (Row Level Security)
-- =====================================

-- Enable Row Level Security
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE interviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE offers ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidate_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_templates ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their organization's data
CREATE POLICY organization_isolation_policy ON jobs
    FOR ALL TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id')::UUID);

CREATE POLICY organization_isolation_policy ON applications
    FOR ALL TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id')::UUID);

CREATE POLICY organization_isolation_policy ON interviews
    FOR ALL TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id')::UUID);

CREATE POLICY organization_isolation_policy ON offers
    FOR ALL TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id')::UUID);

CREATE POLICY organization_isolation_policy ON candidate_profiles
    FOR ALL TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id')::UUID);

CREATE POLICY organization_isolation_policy ON team_invitations
    FOR ALL TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id')::UUID);

CREATE POLICY organization_isolation_policy ON activity_logs
    FOR ALL TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id')::UUID);

CREATE POLICY organization_isolation_policy ON email_templates
    FOR ALL TO authenticated_users
    USING (organization_id = current_setting('app.current_organization_id')::UUID);

-- =====================================
-- COMMENTS & DOCUMENTATION
-- =====================================

COMMENT ON TABLE organizations IS 'Tenant organizations with complete isolation';
COMMENT ON TABLE users IS 'User accounts with role-based access control';
COMMENT ON TABLE jobs IS 'Job postings scoped to organizations';
COMMENT ON TABLE candidate_profiles IS 'Extended candidate profiles with skills and experience';
COMMENT ON TABLE applications IS 'Job applications with status tracking';
COMMENT ON TABLE interviews IS 'Interview schedules and feedback';
COMMENT ON TABLE offers IS 'Job offers and acceptance tracking';
COMMENT ON TABLE team_invitations IS 'Team member invitations with token-based acceptance';
COMMENT ON TABLE activity_logs IS 'Audit trail for all system activities';
COMMENT ON TABLE system_settings IS 'Platform-wide configuration settings';
COMMENT ON TABLE email_templates IS 'Customizable email templates per organization';
COMMENT ON TABLE job_embeddings IS 'AI embeddings for job matching';
COMMENT ON TABLE candidate_embeddings IS 'AI embeddings for candidate matching';

-- Schema version
INSERT INTO system_settings (key, value, description, is_public) VALUES
('schema_version', '1.0', 'Database schema version', false);
