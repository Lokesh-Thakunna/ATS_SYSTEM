import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Briefcase, User, FileText, Star, Search, MapPin, DollarSign,
  TrendingUp, Clock, CheckCircle, Upload, Edit, Eye, Save,
  Building2, ArrowRight, Target, Award
} from 'lucide-react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Input from '../../components/ui/Input';

const CandidateDashboard = () => {
  const [profile, setProfile] = useState(null);
  const [recommendedJobs, setRecommendedJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [stats, setStats] = useState({
    profileViews: 0,
    savedJobs: 0,
    applicationsCount: 0,
    interviewsCount: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Fetch profile
      const profileResponse = await fetch('/api/v1/candidate/profile');
      const profileData = await profileResponse.json();
      setProfile(profileData);

      // Fetch recommended jobs
      const jobsResponse = await fetch('/api/v1/candidate/recommended-jobs?limit=6');
      const jobsData = await jobsResponse.json();
      setRecommendedJobs(jobsData.results || []);

      // Fetch applications
      const appsResponse = await fetch('/api/v1/candidate/applications?limit=5');
      const appsData = await appsResponse.json();
      setApplications(appsData.results || []);

      // Fetch stats
      const statsResponse = await fetch('/api/v1/candidate/stats');
      const statsData = await statsResponse.json();
      setStats(statsData);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getMatchBadge = (matchScore) => {
    if (matchScore >= 90) return <Badge variant="success">Perfect Match</Badge>;
    if (matchScore >= 80) return <Badge variant="success">Excellent Match</Badge>;
    if (matchScore >= 70) return <Badge variant="secondary">Good Match</Badge>;
    if (matchScore >= 60) return <Badge variant="warning">Fair Match</Badge>;
    return <Badge variant="destructive">Poor Match</Badge>;
  };

  const getStatusBadge = (status) => {
    const variants = {
      applied: 'default',
      reviewing: 'secondary',
      interview: 'warning',
      offer: 'success',
      rejected: 'destructive',
      hired: 'success',
      withdrawn: 'secondary'
    };
    return <Badge variant={variants[status] || 'default'}>{status}</Badge>;
  };

  const renderStars = (score) => {
    const fullStars = Math.floor(score / 20);
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`h-4 w-4 ${
          i < fullStars ? 'text-yellow-400 fill-current' : 'text-gray-300'
        }`}
      />
    ));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Job Seeker Dashboard</h1>
          <p className="text-gray-600 mt-1">Find your next opportunity</p>
        </div>
        <div className="flex items-center space-x-3">
          <Link to="/candidate/profile">
            <Button variant="outline" size="sm">
              <Edit className="h-4 w-4 mr-2" />
              Edit Profile
            </Button>
          </Link>
          <Link to="/candidate/jobs">
            <Button>
              <Search className="h-4 w-4 mr-2" />
              Browse Jobs
            </Button>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Section */}
        <Card>
          <div className="p-6">
            <div className="text-center">
              <div className="mx-auto h-20 w-20 rounded-full bg-indigo-100 flex items-center justify-center mb-4">
                <User className="h-10 w-10 text-indigo-600" />
              </div>
              <h2 className="text-lg font-semibold text-gray-900">
                {profile?.first_name} {profile?.last_name}
              </h2>
              <p className="text-sm text-gray-500">{profile?.headline}</p>
              
              <div className="mt-4 space-y-2">
                <div className="flex items-center justify-center text-sm text-gray-600">
                  <MapPin className="h-4 w-4 mr-1" />
                  {profile?.location || 'Location not set'}
                </div>
                <div className="flex items-center justify-center text-sm text-gray-600">
                  <Briefcase className="h-4 w-4 mr-1" />
                  {profile?.experience_years || 0} years experience
                </div>
              </div>
              
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">Profile Completion</span>
                  <span className="text-sm font-medium text-gray-900">
                    {profile?.completion_percentage || 0}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="h-2 rounded-full bg-indigo-600"
                    style={{ width: `${profile?.completion_percentage || 0}%` }}
                  ></div>
                </div>
              </div>
              
              <div className="mt-4 space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Resume Status</span>
                  {profile?.resume_uploaded ? (
                    <Badge variant="success">Active</Badge>
                  ) : (
                    <Badge variant="destructive">Missing</Badge>
                  )}
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Profile Views</span>
                  <span className="font-medium text-gray-900">{stats.profileViews}</span>
                </div>
              </div>
              
              <div className="mt-4 space-y-2">
                <Link to="/candidate/profile">
                  <Button variant="outline" className="w-full">
                    <Edit className="h-4 w-4 mr-2" />
                    Edit Profile
                  </Button>
                </Link>
                {profile?.resume_uploaded ? (
                  <Button variant="outline" className="w-full">
                    <Eye className="h-4 w-4 mr-2" />
                    View Resume
                  </Button>
                ) : (
                  <Button className="w-full">
                    <Upload className="h-4 w-4 mr-2" />
                    Upload Resume
                  </Button>
                )}
              </div>
            </div>
          </div>
        </Card>

        {/* Recommended Jobs */}
        <div className="lg:col-span-2">
          <Card>
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Recommended Jobs</h2>
                <Badge variant="secondary">AI Powered</Badge>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {recommendedJobs.map((job) => (
                  <div key={job.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900 line-clamp-1">{job.title}</h3>
                        <p className="text-sm text-gray-500">{job.organization_name}</p>
                      </div>
                      {getMatchBadge(job.match_score)}
                    </div>
                    
                    <div className="flex items-center text-sm text-gray-600 mb-2">
                      <MapPin className="h-4 w-4 mr-1" />
                      {job.location} • {job.job_type}
                    </div>
                    
                    <div className="flex items-center text-sm text-gray-600 mb-3">
                      <DollarSign className="h-4 w-4 mr-1" />
                      {job.salary_min && job.salary_max 
                        ? `$${job.salary_min.toLocaleString()} - $${job.salary_max.toLocaleString()}`
                        : 'Salary not specified'
                      }
                    </div>
                    
                    <div className="mb-3">
                      <div className="flex items-center mb-1">
                        <span className="text-sm text-gray-600 mr-2">Match:</span>
                        <div className="flex items-center">
                          {renderStars(job.match_score)}
                          <span className="text-sm text-gray-500 ml-1">({job.match_score}%)</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex flex-wrap gap-1">
                        {job.required_skills?.slice(0, 3).map((skill) => (
                          <Badge key={skill} variant="outline" size="sm">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                      <div className="flex items-center space-x-2">
                        <Button variant="ghost" size="sm">
                          <Save className="h-4 w-4" />
                        </Button>
                        <Button size="sm">
                          Apply
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-4 text-center">
                <Link to="/candidate/jobs">
                  <Button variant="outline">
                    View All Recommended Jobs
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                </Link>
              </div>
            </div>
          </Card>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* My Applications */}
        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">My Applications</h2>
              <Link to="/candidate/applications">
                <Button variant="outline" size="sm">View All</Button>
              </Link>
            </div>
            <div className="space-y-4">
              {applications.map((app) => (
                <div key={app.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{app.job_title}</h3>
                    <p className="text-sm text-gray-500">
                      {app.organization_name} • Applied {app.applied_at}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getStatusBadge(app.status)}
                    <Button variant="ghost" size="sm">
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* Application Stats */}
        <Card>
          <div className="p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Application Statistics</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <FileText className="h-5 w-5 text-blue-600 mr-3" />
                  <div>
                    <p className="font-medium text-gray-900">Total Applications</p>
                    <p className="text-sm text-gray-500">All time</p>
                  </div>
                </div>
                <span className="text-2xl font-bold text-gray-900">{stats.applicationsCount}</span>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <Calendar className="h-5 w-5 text-purple-600 mr-3" />
                  <div>
                    <p className="font-medium text-gray-900">Interviews</p>
                    <p className="text-sm text-gray-500">Scheduled</p>
                  </div>
                </div>
                <span className="text-2xl font-bold text-gray-900">{stats.interviewsCount}</span>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <Save className="h-5 w-5 text-green-600 mr-3" />
                  <div>
                    <p className="font-medium text-gray-900">Saved Jobs</p>
                    <p className="text-sm text-gray-500">Bookmarked</p>
                  </div>
                </div>
                <span className="text-2xl font-bold text-gray-900">{stats.savedJobs}</span>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <TrendingUp className="h-5 w-5 text-orange-600 mr-3" />
                  <div>
                    <p className="font-medium text-gray-900">Profile Views</p>
                    <p className="text-sm text-gray-500">Recruiter views</p>
                  </div>
                </div>
                <span className="text-2xl font-bold text-gray-900">{stats.profileViews}</span>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Link to="/candidate/jobs">
              <Button variant="outline" className="w-full justify-start">
                <Search className="h-4 w-4 mr-2" />
                Browse Jobs
              </Button>
            </Link>
            <Link to="/candidate/profile">
              <Button variant="outline" className="w-full justify-start">
                <User className="h-4 w-4 mr-2" />
                Update Profile
              </Button>
            </Link>
            <Link to="/candidate/applications">
              <Button variant="outline" className="w-full justify-start">
                <FileText className="h-4 w-4 mr-2" />
                My Applications
              </Button>
            </Link>
            <Link to="/candidate/saved-jobs">
              <Button variant="outline" className="w-full justify-start">
                <Save className="h-4 w-4 mr-2" />
                Saved Jobs
              </Button>
            </Link>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default CandidateDashboard;
