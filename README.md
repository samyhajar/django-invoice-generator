# Django Invoice Generator

A Django-based invoice generator with PDF export capabilities and a modern admin interface.

## Features

- Create and manage invoices with custom numbering
- Client and project management
- PDF generation with WeasyPrint
- Modern admin interface with django-unfold
- Hierarchical document archiving

## Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/samyhajar/django-invoice-generator.git
   cd django-invoice-generator
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

Visit `http://localhost:8000/admin` to access the admin interface.

## Railway Deployment

### Prerequisites
- GitHub account
- Railway account (sign up at [railway.app](https://railway.app))

### Deployment Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/samyhajar/django-invoice-generator.git
   git push -u origin main
   ```

2. **Deploy on Railway**
   - Go to [Railway](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select `django-invoice-generator`
   - Add PostgreSQL database: Click "New" → "Database" → "PostgreSQL"

3. **Set Environment Variables**
   In Railway dashboard, add:
   - `SECRET_KEY` - Generate a new Django secret key
   - `DEBUG=False`
   - `ALLOWED_HOSTS` - Your Railway domain (e.g., `your-app.railway.app`)

4. **Generate Domain**
   - Go to your service settings in Railway
   - Click "Generate Domain"

5. **Create Superuser** (via Railway CLI or shell)
   ```bash
   railway run python manage.py createsuperuser
   ```

## Tech Stack

- **Framework**: Django 6.0
- **Database**: SQLite (development), PostgreSQL (production)
- **PDF Generation**: WeasyPrint
- **Admin Theme**: django-unfold
- **Deployment**: Railway
- **Web Server**: Gunicorn
- **Static Files**: WhiteNoise

## License

MIT
