# AGENTS.md - Guide for AI Assistants

## Purpose
This document provides guidelines for AI assistants like GitHub Copilot and Claude to understand this repository (techblog_cms) and assist effectively. It clarifies the repository structure, tech stack, and development process to enable AI to generate appropriate code and provide sound advice.

## Repository Overview
techblog_cms is a Django-based technical blog content management system. It operates in a containerized environment using Docker Compose, integrating Nginx reverse proxy, PostgreSQL database, Redis cache, and automated SSL certificate management via Let's Encrypt. The configuration prioritizes security and scalability, aiming for production readiness.

## Technology Stack
- **Backend**: Django 4.2, Python 3.11
- **Database**: PostgreSQL
- **Cache**: Redis
- **Web Server**: Nginx (Reverse Proxy + Static File Delivery)
- **Containerization**: Docker, Docker Compose
- **SSL Certificates**: Let's Encrypt (Certbot)
- **Testing**: pytest, Django Test Framework
- **CI/CD**: GitHub Actions
- **Security**: HTTPS enforcement, security headers, environment variable management
- **Frontend**: HTML/CSS (Tailwind CSS), JavaScript (minimal)

## Project Structure
```
techblog_cms/
├── app/                          # Django application
│   ├── techblog_cms/            # Main Django app
│   │   ├── __init__.py
│   │   ├── settings.py          # Django settings (using environment variables)
│   │   ├── urls.py              # URL mapping
│   │   ├── views.py             # View functions
│   │   ├── wsgi.py              # WSGI entry point
│   │   └── templates/           # HTML templates
│   └── requirements.txt         # Python dependencies
├── nginx/                        # Nginx configuration
│   ├── conf.d/
│   │   └── default.conf         # Nginx configuration file
│   └── Dockerfile               # Nginx container definition
├── scripts/                      # Utility scripts
│   ├── init-letsencrypt.sh      # Initialize SSL certificate
│   └── renew-cert.sh            # Renew SSL certificate
├── static/                       # Static files
├── tests/                        # Test files
├── docker-compose.yml            # Container orchestration
├── Dockerfile.*                  # Various Dockerfiles
├── requirements.txt              # Project-wide dependencies
└── pytest.ini                    # pytest configuration
```

## Development Guidelines

### Coding Standards
- **Python**: PEP 8 compliant, using Black formatter
- **Django**: Follow Django best practices
- **Docker**: Multi-stage builds, security scanning (Trivy)
- **Security**: Manage sensitive info via environment variables, enforce HTTPS

### Environment Variables
Critical settings managed via environment variables:
- `DEBUG`: Debug mode (False in production)
- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ALLOWED_HOSTS`: List of allowed hosts


### Testing
- Unit and integration testing using pytest
- Automated test execution via CI/CD
- Coverage report generation


## Instructions for AI Assistant


### Considerations for Code Generation
1. **Security First**: Use environment variables for sensitive data. Do not hardcode.
2. **Containerization Ready**: Follow Docker best practices to create lightweight images.
3. **Django Best Practices**: Properly separate view functions, models, and templates.
4. **Error Handling**: Implement proper exception handling and log output.
5. **Performance**: Optimize database queries and utilize caching.

### Guidelines for Support
1. **Adding New Features**: Adhere to existing structure. Create migrations as needed.
2. **Bug Fixes**: Add test cases to prevent regressions.
3. **Document Updates**: Update README.md and this AGENTS.md when modifying code.
4. **Dependencies**: Update requirements.txt when adding new packages.
5. **Docker Configuration**: Verify docker-compose.yml and related Dockerfiles when making changes.

### Prohibited Actions
- Hard-coded passwords or API keys
- Inefficient database queries
- Security vulnerabilities (SQL injection, XSS, etc.)
- Adding unnecessary dependencies

### Recommended Tool Usage
- **Code Editing**: `replace_string_in_file` or `insert_edit_into_file`
- **File Creation**: `create_file`
- **Terminal Execution**: run_in_terminal (e.g., Docker commands)
- **Test Execution**: runTests
- **File Search**: grep_search or semantic_search

## Contribution Guide
1. Create a feature branch from the develop branch
2. If the current branch is main, create the feature branch from main.
2. Implement changes and add tests.
3. Create a pull request and request a review.
4. After merging, update documentation as needed.

## Contact
Please use GitHub Issues or Pull Requests for questions or improvement suggestions.

---
Last updated: August 31, 2025
