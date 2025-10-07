
from django.db import models
from django.utils import timezone

class Registration(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    contact = models.CharField(max_length=15)
    gender = models.CharField(max_length=10, choices=[("male", "Male"), ("female", "Female"), ("other", "Other")])

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Mcq(models.Model):
    topic = models.CharField(max_length=100)
    subtopic = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=20, choices=[("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")])
    question_no = models.IntegerField()
    question = models.TextField()
    option1 = models.CharField(max_length=255)
    option2 = models.CharField(max_length=255)
    option3 = models.CharField(max_length=255)
    option4 = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=1, choices=[("1", "Option 1"), ("2", "Option 2"), ("3", "Option 3"), ("4", "Option 4")])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.topic} - {self.subtopic} (Q{self.question_no})"

class QuizResult(models.Model):
    user = models.ForeignKey(Registration, on_delete=models.CASCADE)
    topic = models.CharField(max_length=100)
    subtopic = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=20)
    date_attempted = models.DateTimeField(default=timezone.now)
    total_questions = models.IntegerField()
    correct_questions = models.IntegerField()
    wrong_questions = models.IntegerField()
    score = models.FloatField()

    def __str__(self):
        return f"{self.user.first_name} - {self.topic} - {self.score}%"
