import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Briefcase, Users, Calendar, FileText, Plus, Search, Filter,
  Star, Clock, CheckCircle, AlertCircle, TrendingUp, Eye,
  MessageSquare, Send, XCircle, ArrowUp, ArrowDown
} from 'lucide-react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Input from '../../components/ui/Input';

const RecruiterDashboard = () => {
  const [metrics, setMetrics] = useState({
    activeJobs: { count: 0, change: 0 },
    applications: { count: 0, change: 0 },
    interviews: { count: 0, change: 0 },
    offers: { count: 0, change: 0 }
  });
  
  const [recentJobs, setRecentJobs] = useState([]);
  const [recentApplications, setRecentApplications] = useState([]);
  const [matchedCandidates, setMatchedCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Fetch metrics
      const metricsResponse = await fetch('/api/v1/recruiter/metrics');
      const metricsData = await metricsResponse.json();
      setMetrics(metricsData);

      // Fetch recent jobs
      const jobsResponse = await fetch('/api/v1/recruiter/jobs?limit=5');
      const jobsData = await jobsResponse.json();
      setRecentJobs(jobsData.results || []);

      // Fetch recent applications
      const appsResponse = await fetch('/api/v1/recruiter/applications?limit=5');
      const appsData = await appsResponse.json();
      setRecentApplications(appsData.results || []);

      // Fetch AI matched candidates
      const matchesResponse = await fetch('/api/v1/recruiter/matched-candidates?limit=5');
      const matchesData = await matchesResponse.json();
      setMatchedCandidates(matchesData.results || []);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const MetricCard = ({ title, value, change, icon: Icon, color = 'blue' }) => (
    <Card className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <div className="flex items-center mt-2">
            {change > 0 ? (
              <ArrowUp className="h-4 w-4 text-green-500 mr-1" />
            ) : change < 0 ? (
              <ArrowDown className="h-4 w-4 text-red-500 mr-1" />
            ) : null}
            <span className={`text-sm ${
              change > 0 ? 'text-green-600' : 
              change < 0 ? 'text-red-600' : 'text-gray-600'
            }`}>
              {change > 0 ? '+' : ''}{change} new
            </span>
          </div>
        </div>
        <div className={`p-3 rounded-full bg-${color}-100`}>
          <Icon className={`h-6 w-6 text-${color}-600`} />
        </div>
      </div>
    </Card>
  );

  const getStatusBadge = (status) => {
    const variants = {
      active: 'success',
      draft: 'secondary',
      closed: 'destructive',
      applied: 'default',
      reviewing: 'secondary',
      interview: 'warning',
      offer: 'success',
      rejected: 'destructive'
    };
    return <Badge variant={variants[status] || 'default'}>{status}</Badge>;
  };

  const getFitBadge = (fitLabel) => {
    const variants = {
      perfect: 'success',
      excellent: 'success',
      good: 'secondary',
      fair: 'warning',
      poor: 'destructive'
    };
    return <Badge variant={variants[fitLabel] || 'default'}>{fitLabel}</Badge>;
  };

  const renderStars = (rating) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`h-4 w-4 ${
          i < Math.floor(rating) ? 'text-yellow-400 fill-current' : 'text-gray-300'
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
          <h1 className="text-3xl font-bold text-gray-900">Recruiter Dashboard</h1>
          <p className="text-gray-600 mt-1">Manage your jobs and applications</p>
        </div>
        <div className="flex items-center space-x-3">
          <Link to="/recruiter/jobs/create">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Post New Job
            </Button>
          </Link>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Active Jobs"
          value={metrics.activeJobs.count}
          change={metrics.activeJobs.change}
          icon={Briefcase}
          color="blue"
        />
        <MetricCard
          title="Applications"
          value={metrics.applications.count}
          change={metrics.applications.change}
          icon={FileText}
          color="green"
        />
        <MetricCard
          title="Interviews"
          value={metrics.interviews.count}
          change={metrics.interviews.change}
          icon={Calendar}
          color="purple"
        />
        <MetricCard
          title="Offers Sent"
          value={metrics.offers.count}
          change={metrics.offers.change}
          icon={Send}
          color="orange"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Jobs */}
        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">My Jobs</h2>
              <Link to="/recruiter/jobs">
                <Button variant="outline" size="sm">View All</Button>
              </Link>
            </div>
            <div className="space-y-4">
              {recentJobs.map((job) => (
                <div key={job.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{job.title}</h3>
                    <p className="text-sm text-gray-500">
                      Posted {job.posted_at} • {job.applications_count} applications
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getStatusBadge(job.status)}
                    <Link to={`/recruiter/jobs/${job.id}`}>
                      <Button variant="ghost" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* Recent Applications */}
        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Recent Applications</h2>
              <Link to="/recruiter/applications">
                <Button variant="outline" size="sm">View All</Button>
              </Link>
            </div>
            <div className="space-y-4">
              {recentApplications.map((app) => (
                <div key={app.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h3 className="font-medium text-gray-900">{app.candidate_name}</h3>
                      <div className="flex items-center">
                        {renderStars(app.rating || 0)}
                        <span className="text-sm text-gray-500 ml-1">({app.rating || 0})</span>
                      </div>
                    </div>
                    <p className="text-sm text-gray-500">
                      {app.job_title} • Applied {app.applied_at}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getStatusBadge(app.status)}
                    <div className="flex items-center space-x-1">
                      <Button variant="ghost" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <MessageSquare className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Matched Candidates */}
        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">AI Matched Candidates</h2>
              <Badge variant="secondary">AI Powered</Badge>
            </div>
            <div className="space-y-4">
              {matchedCandidates.map((match) => (
                <div key={match.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-medium text-gray-900">{match.candidate_name}</h3>
                      <p className="text-sm text-gray-500">{match.current_title}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-indigo-600">{match.match_score}%</div>
                      {getFitBadge(match.fit_label)}
                    </div>
                  </div>
                  
                  <div className="mb-3">
                    <div className="flex flex-wrap gap-1">
                      {match.skills_details?.matched_skills?.slice(0, 4).map((skill) => (
                        <Badge key={skill} variant="outline" size="sm">
                          {skill}
                        </Badge>
                      ))}
                      {match.skills_details?.matched_skills?.length > 4 && (
                        <Badge variant="outline" size="sm">
                          +{match.skills_details.matched_skills.length - 4} more
                        </Badge>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-600">
                      {match.experience_years} years experience
                    </p>
                    <div className="flex items-center space-x-2">
                      <Button variant="outline" size="sm">
                        <Eye className="h-4 w-4 mr-1" />
                        View Profile
                      </Button>
                      <Button size="sm">
                        <Send className="h-4 w-4 mr-1" />
                        Invite
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* Hiring Pipeline */}
        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Hiring Pipeline</h2>
              <Link to="/recruiter/pipeline">
                <Button variant="outline" size="sm">View Pipeline</Button>
              </Link>
            </div>
            
            <div className="space-y-4">
              {[
                { stage: 'Applied', count: 47, color: 'blue', icon: FileText },
                { stage: 'Reviewing', count: 32, color: 'yellow', icon: Search },
                { stage: 'Interview', count: 8, color: 'purple', icon: Calendar },
                { stage: 'Offer', count: 3, color: 'green', icon: Send },
                { stage: 'Hired', count: 1, color: 'emerald', icon: CheckCircle }
              ].map((stage) => (
                <div key={stage.stage} className="flex items-center">
                  <div className={`p-2 rounded-full bg-${stage.color}-100 mr-3`}>
                    <stage.icon className={`h-4 w-4 text-${stage.color}-600`} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-900">{stage.stage}</span>
                      <span className="text-sm text-gray-500">{stage.count} candidates</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full bg-${stage.color}-500`}
                        style={{ width: `${(stage.count / 47) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Link to="/recruiter/jobs/create">
              <Button variant="outline" className="w-full justify-start">
                <Briefcase className="h-4 w-4 mr-2" />
                Create Job
              </Button>
            </Link>
            <Link to="/recruiter/candidates/search">
              <Button variant="outline" className="w-full justify-start">
                <Search className="h-4 w-4 mr-2" />
                Search Candidates
              </Button>
            </Link>
            <Link to="/recruiter/interviews/schedule">
              <Button variant="outline" className="w-full justify-start">
                <Calendar className="h-4 w-4 mr-2" />
                Schedule Interview
              </Button>
            </Link>
            <Link to="/recruiter/analytics">
              <Button variant="outline" className="w-full justify-start">
                <TrendingUp className="h-4 w-4 mr-2" />
                View Analytics
              </Button>
            </Link>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default RecruiterDashboard;
