from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),  # Home page
    path("register/", views.register, name="register"),  # Registration page
    path("login/", views.login, name="login"),  # Login page
    path("success/", views.success, name="success"),  # Success page after registration
    path("userdashboard/", views.userdashboard, name="userdashboard"),  # User dashboard
    path("logout/", views.userlogout, name="userlogout"),  # Logout
    path('adminlogin/', views.admin_login, name='admin_login'),
    path('admindashboard/', views.admindashboard, name='admindashboard'),
    path('adminlogout/', views.admin_logout, name='admin_logout'),
    path('upload-mcq/', views.upload_mcq_pdf, name='upload_mcq'),
    path('database/', views.database_view, name='database'),
    path("start-quiz/", views.start_quiz, name="start_quiz"),  # 🔑 This must exist
    path("submit-quiz/", views.submit_quiz, name="submit_quiz"),
    path('accounts/login/', views.login), 
    path("history/", views.history, name="history"),
    path("results/", views.results, name="results"),
    path("dashboard/", views.analytics_dashboard, name="dashboard"),
    path("suggestions/", views.suggestions_view, name="suggestions"),



]

