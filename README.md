# 🧠 SmartQuizzer

SmartQuizzer is a Django-based web application designed to deliver dynamic MCQ quizzes with real-time result tracking, user dashboards, and accessibility-first design. Built for students, educators, and developers preparing for competitive exams, it blends clean UI with scalable backend logic.

## 🚀 Features

- 🔐 **User & Admin Dashboards**  
  Separate views for users and admins with role-based access.

- 📝 **MCQ Quiz Engine**  
  Supports multiple subjects with correct answer validation and scoring.

- 📊 **Result Tracking**  
  Users can view detailed quiz results and performance history.

- 🧩 **Modular Architecture**  
  Clean separation of models, views, templates, and utilities.

- ♿ **Accessibility-First Design**  
  Templates optimized for screen readers, keyboard navigation, and visual clarity.

---

## 🛠️ Tech Stack

| Layer        | Technology            |
|--------------|------------------------|
| Backend      | Django (Python)        |
| Database     | SQLite                 |
| Frontend     | HTML, CSS              |
| Templates    | Django Templating      |
| Versioning   | Git + GitHub           |


## 📂 Project Structure
smartquizzer/
├── base/                      # Core app for quiz logic
│   ├── __init__.py
│   ├── admin.py              # Admin panel configuration
│   ├── apps.py
│   ├── models.py             # Quiz models (questions, results, users)
│   ├── views.py              # View functions for user/admin flows
│   ├── urls.py               # URL routing for base app
│   ├── templates/            # HTML templates
│   │   ├── base/
│   │   │   ├── index.html
│   │   │   ├── quiz.html
│   │   │   ├── result.html
│   │   │   └── dashboard.html
│   └── static/               # CSS, JS, images
│       ├── css/
│       ├── js/
│       └── images/
├── mysqldbconnect/           # Django project config
│   ├── __init__.py
│   ├── settings.py           # Project settings
│   ├── urls.py               # Root URL config
│   └── wsgi.py
├── db.sqlite3                # Local database
├── manage.py                 # Django CLI utility
├── .gitignore                # Git exclusions
├── LICENSE                   # MIT License
└── README.md                 # Project overview and setup

## ⚙️ Setup Instructions

1. **Clone the repo**  
   ```bash
   git clone https://github.com/Soundarya132/smartquizzer.git
   cd smartquizzer
   
2.**Create virtual environment**
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

3. **Install dependencies**
   pip install -r requirements.txt
   
4.**Run migrations**
   python manage.py makemigrations
python manage.py migrate

5.**Start the server**
   python manage.py runserver

6.**Access the app**
Open http://127.0.0.1:8000/ in your browser.
