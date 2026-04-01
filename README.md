# ATS (Applicant Tracking System) Backend

## Features

- **User Management**: Candidate and recruiter registration/login
- **Job Management**: Create, update, and manage job postings
- **AI-Powered Matching**: Semantic job-resume matching using SentenceTransformers
- **Resume Processing**: PDF/DOCX parsing with skill and experience extraction
- **File Storage**: Supabase integration with local fallback
- **Security**: JWT authentication, input validation, rate limiting
- **Monitoring**: Health checks, logging, and error tracking

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL with pgvector extension
- Supabase account (optional, can use local storage)

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd ats_project/backend
   ```
2. **Create virtual environment**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```
3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```
4. **Environment Configuration**

   ```bash
   cp .env.example .env
   # Edit .env with your actual configuration
   ```
5. **Database Setup**

   ```bash
   python manage.py migrate
   ```
6. **Create superuser (optional)**

   ```bash
   python manage.py createsuperuser
   ```
7. **Run the server**

   ```bash
   python manage.py runserver
   ```

## Environment Variables

Create a `.env` file with the following variables:

```env
# Django Security Settings
SECRET_KEY=your-secret-key-here-change-this-in-production
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key-here

# Database Configuration
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=your-database-host.com
DB_PORT=5432
```

## Security Notes

⚠️ **Important**: Never commit actual credentials to version control. The `.env.example` file contains placeholder values only.

### Security Features

- JWT authentication with secure token handling
- Input validation and sanitization
- Rate limiting on API endpoints
- Security headers and middleware
- SQL injection protection
- XSS protection
- CSRF protection

### Production Deployment

For production deployment:

1. Set `DEBUG=False`
2. Use a strong, unique `SECRET_KEY`
3. Configure `ALLOWED_HOSTS` properly
4. Enable HTTPS and security headers
5. Use environment variables for all secrets
6. Set up proper logging and monitoring
7. Use a production-grade database
8. Implement backup strategies

## API Documentation

API documentation is available at `/api/docs/` when the server is running.

### Health Checks

- `/health/` - Basic health check
- `/health/detailed/` - Detailed health check with system metrics

## Development

### Running Tests

```bash
python manage.py test
```

### Code Quality

```bash
# Install development dependencies
pip install black flake8 mypy

# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## Project Structure

```
backend/
├── ats_backend/           # Main Django project
│   ├── settings.py       # Django settings
│   ├── urls.py          # URL configuration
│   └── wsgi.py          # WSGI application
├── authentication/       # User authentication app
├── candidates/          # Candidate management
├── jobs/                # Job postings and applications
├── resumes/             # Resume processing and storage
├── matching/            # AI-powered job matching
├── services/            # External services (parsing)
├── core/                # Shared utilities and middleware
└── logs/                # Application logs
```

## Contributing

1. Follow Django best practices
2. Write tests for new features
3. Use proper error handling
4. Update documentation
5. Follow security guidelines

## License

[Add your license information here]

## Support

For support, please contact [contact information] or create an issue in the repository.
