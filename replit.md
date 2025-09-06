# Django POS (Point of Sale) System

## Overview
This is a comprehensive Django-based Point of Sale (POS) system imported from GitHub and configured to run in the Replit environment. The application includes inventory management, sales tracking, purchase orders, customer/supplier management, financial reporting, and user authentication.

## Current State
- ✅ Django 5.1.3 application successfully running
- ✅ Database migrations completed (SQLite for development)
- ✅ Static files collected and served
- ✅ Development server running on port 5000
- ✅ Deployment configuration set for production

## Recent Changes (September 6, 2025)
- Configured Django application for Replit environment
- Fixed PIL/Pillow compatibility issues with temporary workaround
- Set up development server workflow on port 5000
- Configured deployment settings for autoscale deployment
- Temporarily disabled PDF export functions due to reportlab/PIL conflicts

## Project Architecture
- **Backend**: Django 5.1.3 with SQLite database (development)
- **Frontend**: Bootstrap-based responsive UI with modern POS interface
- **Static Files**: Managed with WhiteNoise for production deployment
- **Authentication**: Custom user authentication with role-based access

## Apps Structure
- `admin/` - Django project configuration
- `authentication/` - User authentication and role management
- `inventory/` - Product, category, and stock management
- `sales/` - Order processing and sales management
- `purchases/` - Purchase order and supplier management
- `people/` - Customer and supplier management
- `finance/` - Financial tracking and expense management
- `reports/` - Business reporting and analytics
- `content/` - Content management features
- `landing/` - Landing page and public interface

## Known Issues
- PDF export functionality temporarily disabled due to PIL _imaging module compatibility issues
- ImageField validation bypassed for development setup (requires PIL fix for production)

## Development Notes
- Server runs on 0.0.0.0:5000 for Replit compatibility
- ALLOWED_HOSTS configured for all hosts ('*')
- CSRF_TRUSTED_ORIGINS configured for production domains
- Static files served via WhiteNoise middleware

## User Preferences
- Keep existing project structure and Django conventions
- Maintain responsive Bootstrap UI design
- Preserve business logic and POS functionality
- Use SQLite for development, support PostgreSQL for production