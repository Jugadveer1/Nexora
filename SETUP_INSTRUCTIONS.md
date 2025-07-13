# Nexora Project Setup Instructions

## Overview
This document provides step-by-step instructions for setting up the Nexora Django web application development environment.

## Prerequisites
- Python 3.8 or higher installed on your system
- Git (for version control)
- Windows Command Prompt or PowerShell

## Quick Setup (Automated)

### Option 1: Using the Setup Script
1. Open Command Prompt in the project directory
2. Run the automated setup script:
   ```cmd
   setup_environment.bat
   ```
3. The script will automatically:
   - Create a virtual environment
   - Install all required dependencies
   - Run Django system checks
   - Collect static files

### Option 2: Manual Setup

#### Step 1: Create Virtual Environment
```cmd
python -m venv venv
```

#### Step 2: Activate Virtual Environment
```cmd
venv\Scripts\activate
```

#### Step 3: Upgrade pip
```cmd
python -m pip install --upgrade pip
```

#### Step 4: Install Dependencies
```cmd
pip install -r requirements.txt
```

#### Step 5: Run Django Checks
```cmd
python manage.py check
```

#### Step 6: Collect Static Files
```cmd
python manage.py collectstatic --noinput
```

## Running the Application

### Start Development Server
```cmd
# Make sure virtual environment is activated
venv\Scripts\activate

# Start the Django development server
python manage.py runserver
```

The application will be available at: `http://127.0.0.1:8000/`

### Quick Activation
For future development sessions, you can use:
```cmd
activate_venv.bat
```

## Project Dependencies

The `requirements.txt` file includes all necessary packages:

### Core Framework
- **Django 5.2** - Main web framework
- **django-cors-headers** - CORS handling for API requests

### AI Integration
- **groq** - AI chatbot integration
- **pydantic** - Data validation for AI responses

### File Handling
- **Pillow** - Image processing
- **reportlab** - PDF generation

### Deployment
- **gunicorn** - WSGI HTTP Server
- **whitenoise** - Static file serving

### Utilities
- **requests** - HTTP library
- **python-dotenv** - Environment variable management
- **python-dateutil** - Date/time utilities

## Common Django Commands

```cmd
# Check for issues
python manage.py check

# Create database migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run development server
python manage.py runserver

# Run with specific port
python manage.py runserver 8080
```

## Troubleshooting

### Virtual Environment Issues
- If activation fails, ensure you're in the correct directory
- On some systems, you might need to use `venv\Scripts\activate.bat` instead

### Package Installation Issues
- Ensure pip is up to date: `python -m pip install --upgrade pip`
- If Pillow installation fails, you might need Visual Studio Build Tools

### Django Issues
- Run `python manage.py check` to identify configuration problems
- Ensure all environment variables are properly set

## Environment Variables
Create a `.env` file in the project root with:
```
DEBUG=True
SECRET_KEY=your-secret-key-here
GROQ_API_KEY=your-groq-api-key-here
```

## Development Workflow
1. Activate virtual environment: `activate_venv.bat`
2. Make your changes
3. Test with: `python manage.py runserver`
4. Run checks: `python manage.py check`
5. Commit your changes

## Support
If you encounter any issues during setup, please check:
1. Python version compatibility (3.8+)
2. All dependencies are installed correctly
3. Virtual environment is activated
4. Environment variables are configured

For additional help, refer to the Django documentation or project maintainers.
