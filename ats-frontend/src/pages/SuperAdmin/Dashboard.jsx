import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Building2, Users, Briefcase, FileText, TrendingUp, 
  Activity, AlertCircle, CheckCircle, Clock, DollarSign,
  ArrowUp, ArrowDown, MoreHorizontal, Settings, LogOut
} from 'lucide-react';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';

const SuperAdminDashboard = () => {
  const [metrics, setMetrics] = useState({
    organizations: { count: 0, growth: 0 },
    users: { count: 0, growth: 0 },
    jobs: { count: 0, growth: 0 },
    applications: { count: 0, growth: 0 },
    revenue: { amount: 0, growth: 0 }
  });
  
  const [systemHealth, setSystemHealth] = useState({
    api: 'healthy',
    database: 'healthy',
    email: 'healthy',
    cache: 'healthy',
    storage: 85,
    uptime: 99.8
  });
  
  const [topOrganizations, setTopOrganizations] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Fetch platform metrics
      const metricsResponse = await fetch('/api/v1/admin/platform-metrics');
      const metricsData = await metricsResponse.json();
      setMetrics(metricsData);

      // Fetch system health
      const healthResponse = await fetch('/api/v1/admin/system-health');
      const healthData = await healthResponse.json();
      setSystemHealth(healthData);

      // Fetch top organizations
      const orgsResponse = await fetch('/api/v1/admin/top-organizations');
      const orgsData = await orgsResponse.json();
      setTopOrganizations(orgsData);

      // Fetch recent activity
      const activityResponse = await fetch('/api/v1/admin/recent-activity');
      const activityData = await activityResponse.json();
      setRecentActivity(activityData);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const MetricCard = ({ title, value, growth, icon: Icon, color = 'blue' }) => (
    <Card className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <div className="flex items-center mt-2">
            {growth > 0 ? (
              <ArrowUp className="h-4 w-4 text-green-500 mr-1" />
            ) : (
              <ArrowDown className="h-4 w-4 text-red-500 mr-1" />
            )}
            <span className={`text-sm ${growth > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {growth > 0 ? '+' : ''}{growth}%
            </span>
          </div>
        </div>
        <div className={`p-3 rounded-full bg-${color}-100`}>
          <Icon className={`h-6 w-6 text-${color}-600`} />
        </div>
      </div>
    </Card>
  );

  const HealthStatus = ({ status, label }) => {
    const statusColors = {
      healthy: 'green',
      warning: 'yellow',
      error: 'red'
    };
    
    return (
      <div className="flex items-center justify-between py-2">
        <span className="text-sm text-gray-600">{label}</span>
        <Badge 
          variant={status === 'healthy' ? 'success' : status === 'warning' ? 'warning' : 'destructive'}
          size="sm"
        >
          {status}
        </Badge>
      </div>
    );
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
          <h1 className="text-3xl font-bold text-gray-900">Platform Dashboard</h1>
          <p className="text-gray-600 mt-1">Monitor your ATS platform performance</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" size="sm">
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
          <Button variant="outline" size="sm">
            <LogOut className="h-4 w-4 mr-2" />
            Logout
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        <MetricCard
          title="Organizations"
          value={metrics.organizations.count}
          growth={metrics.organizations.growth}
          icon={Building2}
          color="blue"
        />
        <MetricCard
          title="Active Users"
          value={metrics.users.count}
          growth={metrics.users.growth}
          icon={Users}
          color="green"
        />
        <MetricCard
          title="Total Jobs"
          value={metrics.jobs.count}
          growth={metrics.jobs.growth}
          icon={Briefcase}
          color="purple"
        />
        <MetricCard
          title="Applications"
          value={metrics.applications.count}
          growth={metrics.applications.growth}
          icon={FileText}
          color="orange"
        />
        <MetricCard
          title="Revenue"
          value={`$${metrics.revenue.amount.toLocaleString()}`}
          growth={metrics.revenue.growth}
          icon={DollarSign}
          color="emerald"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Organizations */}
        <Card className="lg:col-span-2">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Top Organizations</h2>
              <Link to="/admin/organizations">
                <Button variant="outline" size="sm">View All</Button>
              </Link>
            </div>
            <div className="space-y-4">
              {topOrganizations.map((org, index) => (
                <div key={org.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="flex items-center justify-center w-8 h-8 bg-indigo-100 rounded-full text-indigo-600 font-semibold text-sm">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{org.name}</p>
                      <p className="text-sm text-gray-500">
                        {org.jobs_count} jobs • {org.applications_count} applications
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{org.users_count} users</p>
                    <p className="text-xs text-gray-500">Active</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* System Health */}
        <Card>
          <div className="p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">System Health</h2>
            <div className="space-y-3">
              <HealthStatus status={systemHealth.api} label="API Status" />
              <HealthStatus status={systemHealth.database} label="Database" />
              <HealthStatus status={systemHealth.email} label="Email Service" />
              <HealthStatus status={systemHealth.cache} label="Cache" />
              
              <div className="pt-3 border-t border-gray-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">Storage Usage</span>
                  <span className="text-sm font-medium text-gray-900">{systemHealth.storage}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${
                      systemHealth.storage > 90 ? 'bg-red-500' : 
                      systemHealth.storage > 70 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${systemHealth.storage}%` }}
                  ></div>
                </div>
              </div>
              
              <div className="pt-3 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Platform Uptime</span>
                  <span className="text-sm font-medium text-gray-900">{systemHealth.uptime}%</span>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
              <Button variant="outline" size="sm">View All</Button>
            </div>
            <div className="space-y-3">
              {recentActivity.map((activity, index) => (
                <div key={index} className="flex items-start space-x-3">
                  <div className={`p-2 rounded-full ${
                    activity.type === 'success' ? 'bg-green-100' :
                    activity.type === 'warning' ? 'bg-yellow-100' :
                    activity.type === 'error' ? 'bg-red-100' : 'bg-blue-100'
                  }`}>
                    {activity.type === 'success' && <CheckCircle className="h-4 w-4 text-green-600" />}
                    {activity.type === 'warning' && <AlertCircle className="h-4 w-4 text-yellow-600" />}
                    {activity.type === 'error' && <AlertCircle className="h-4 w-4 text-red-600" />}
                    {activity.type === 'info' && <Activity className="h-4 w-4 text-blue-600" />}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-900">{activity.description}</p>
                    <p className="text-xs text-gray-500">{activity.timestamp}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* Quick Actions */}
        <Card>
          <div className="p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="grid grid-cols-2 gap-4">
              <Link to="/admin/organizations/create">
                <Button className="w-full justify-start">
                  <Building2 className="h-4 w-4 mr-2" />
                  Create Organization
                </Button>
              </Link>
              <Link to="/admin/users/create">
                <Button variant="outline" className="w-full justify-start">
                  <Users className="h-4 w-4 mr-2" />
                  Add Admin User
                </Button>
              </Link>
              <Link to="/admin/logs">
                <Button variant="outline" className="w-full justify-start">
                  <FileText className="h-4 w-4 mr-2" />
                  View Logs
                </Button>
              </Link>
              <Link to="/admin/settings">
                <Button variant="outline" className="w-full justify-start">
                  <Settings className="h-4 w-4 mr-2" />
                  System Settings
                </Button>
              </Link>
              <Link to="/admin/email-queue">
                <Button variant="outline" className="w-full justify-start">
                  <Activity className="h-4 w-4 mr-2" />
                  Email Queue
                </Button>
              </Link>
              <Link to="/admin/monitoring">
                <Button variant="outline" className="w-full justify-start">
                  <TrendingUp className="h-4 w-4 mr-2" />
                  API Monitoring
                </Button>
              </Link>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default SuperAdminDashboard;
