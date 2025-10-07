from django.contrib import admin
from .models import Registration, Mcq, QuizResult

# Admin for MCQ
@admin.register(Mcq)
class McqAdmin(admin.ModelAdmin):
    list_display = ("topic", "subtopic", "difficulty", "question_no", "question", "correct_answer")
    search_fields = ("topic", "subtopic", "question")
    list_filter = ("topic", "difficulty")

# Register the rest safely
@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "contact", "gender")
    search_fields = ("first_name", "last_name", "email")

@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ("user", "topic", "subtopic", "difficulty", "score", "date_attempted")
    search_fields = ("user__first_name", "topic", "subtopic")
