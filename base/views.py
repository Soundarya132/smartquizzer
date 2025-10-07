import random
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone

from .forms import RegistrationForm, LoginForm, MCQUploadForm
from .models import Registration, Mcq, QuizResult
from .utils import extract_mcqs_from_pdf

logger = logging.getLogger(__name__)

# ---------- Home ----------
def home(request):
    return render(request, "home.html")

# ---------- Registration ----------
@csrf_protect
def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.password = make_password(form.cleaned_data['password'])
                user.save()
                messages.success(request, "Registration successful!")
                return redirect("success")
            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                messages.error(request, "Registration failed. Please try again.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegistrationForm()
    return render(request, "register.html", {"form": form})

# ---------- Login ----------
@csrf_protect
def login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            try:
                user = Registration.objects.get(email=email)
                if check_password(password, user.password):
                    request.session["user_id"] = user.id
                    request.session["user_email"] = user.email
                    messages.success(request, "Login successful!")
                    return redirect("userdashboard")
                else:
                    messages.error(request, "Invalid Email or Password.")
            except Registration.DoesNotExist:
                messages.error(request, "Invalid Email or Password.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})

# ---------- Success ----------
def success(request):
    return render(request, "success.html")

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def custom_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("user_id"):
            messages.warning(request, "Please log in first.")
            return redirect("login")  # your custom login page
        return view_func(request, *args, **kwargs)
    return wrapper

# ---------- views.py ----------
from django.shortcuts import render, redirect
from django.db.models import Avg, Count
from .models import Registration, Mcq, QuizResult
from .decorators import custom_login_required


# ---------- User Dashboard ----------
@custom_login_required
def userdashboard(request):
    user = Registration.objects.get(id=request.session["user_id"])

    # Distinct lists for dropdowns
    topics = Mcq.objects.values_list("topic", flat=True).distinct().order_by("topic")
    subtopics = Mcq.objects.values_list("subtopic", flat=True).distinct().order_by("subtopic")
    difficulties = Mcq.objects.values_list("difficulty", flat=True).distinct().order_by("difficulty")

    # User’s quiz history
    results = QuizResult.objects.filter(user=user).order_by("-date_attempted")

    # Quiz summary (per topic & subtopic)
    quiz_summary = (
        QuizResult.objects.filter(user=user)
        .values("topic", "subtopic")
        .annotate(
            quizzes_taken=Count("id"),
            avg_score=Avg("score"),
        )
        .order_by("topic", "subtopic")
    )

    # ---------- Suggestion Logic ----------
    suggestion = None

    # Count quizzes per difficulty with average score
    difficulty_summary = (
        QuizResult.objects.filter(user=user)
        .values("difficulty")
        .annotate(
            quizzes_taken=Count("id"),
            avg_score=Avg("score"),
        )
    )

    # Convert to dict for quick lookup
    difficulty_stats = {row["difficulty"]: row for row in difficulty_summary}

    # Easy → Medium
    if (
        "easy" in difficulty_stats
        and difficulty_stats["easy"]["quizzes_taken"] >= 5
        and difficulty_stats["easy"]["avg_score"] >= 80
    ):
        suggestion = "🎯 Great job! Try moving up to <b>Medium level</b> quizzes."

    # Medium → Hard
    elif (
        "medium" in difficulty_stats
        and difficulty_stats["medium"]["quizzes_taken"] >= 5
        and difficulty_stats["medium"]["avg_score"] >= 75
    ):
        suggestion = "🚀 Awesome! You’re ready for <b>Hard level</b> quizzes."

    # Hard → Next Topic
    elif (
        "hard" in difficulty_stats
        and difficulty_stats["hard"]["quizzes_taken"] >= 3
        and difficulty_stats["hard"]["avg_score"] >= 80
    ):
        suggestion = "🔥 Excellent work! Move on to the <b>next topic</b>."

    else:
        suggestion = "💪 Keep practicing! Complete more quizzes  to unlock new suggestions."

    # ---------- Context ----------
    context = {
        "user": user,
        "results": results,
        "quiz_summary": quiz_summary,
        "topics": list(topics),
        "subtopics": list(subtopics),
        "difficulties": list(difficulties),
        "suggestion": suggestion,  # ✅ AI suggestion passed to template
    }

    return render(request, "userdashboard.html", context)


# ---------- Start Quiz ----------
# @login_required
def start_quiz(request):
    if request.method == "POST":
        topic = request.POST.get("topic")
        subtopic = request.POST.get("subtopic")
        difficulty = request.POST.get("difficulty")
        num_questions = int(request.POST.get("num_questions", 5))

        questions = list(Mcq.objects.filter(
            topic=topic,
            subtopic=subtopic,
            difficulty=difficulty
        ))

        if len(questions) < num_questions:
            num_questions = len(questions)

        if not questions:
            messages.warning(request, "No questions available for this selection.")
            return redirect("userdashboard")

        selected_questions = random.sample(questions, num_questions)

        request.session['quiz_questions'] = [q.id for q in selected_questions]
        request.session['quiz_meta'] = {
            "topic": topic,
            "subtopic": subtopic,
            "difficulty": difficulty,
            "num_questions": num_questions,
        }

        context = {
            "questions": selected_questions,
            "num_questions": num_questions,
        }
        return render(request, "quiz.html", context)
    else:
        return redirect("userdashboard")

# ---------- Submit Quiz ----------
# @login_required
def submit_quiz(request):
    if request.method == "POST":
        user = Registration.objects.get(id=request.session["user_id"])

        quiz_question_ids = request.session.get('quiz_questions', [])
        quiz_meta = request.session.get('quiz_meta', {})
        if not quiz_question_ids or not quiz_meta:
            messages.error(request, "Quiz session expired.")
            return redirect("userdashboard")

        questions = Mcq.objects.filter(id__in=quiz_question_ids)

        total_questions = len(quiz_question_ids)
        correct = 0
        wrong = 0

        for q in questions:
            selected = request.POST.get(f"question_{q.id}")
            if selected == q.correct_answer:
                correct += 1
            else:
                wrong += 1

        score = (correct / total_questions) * 100 if total_questions else 0

        QuizResult.objects.create(
            user=user,
            topic=quiz_meta.get("topic", ""),
            subtopic=quiz_meta.get("subtopic", ""),
            difficulty=quiz_meta.get("difficulty", ""),
            date_attempted=timezone.now(),
            total_questions=total_questions,
            correct_questions=correct,
            wrong_questions=wrong,
            score=score,
        )

        request.session.pop('quiz_questions', None)
        request.session.pop('quiz_meta', None)

        return render(request, "result.html", {
            "total": total_questions,
            "correct": correct,
            "wrong": wrong,
            "score": round(score, 2),
        })
    else:
        return redirect("userdashboard")

# ---------- Logout ----------
def userlogout(request):
    try:
        request.session.flush()
        messages.success(request, "Logged out successfully.")
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
    return redirect("login")

# ---------- Admin Login ----------
@csrf_protect
def admin_login(request):
    if request.session.get("is_admin"):
        return redirect("admindashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        if username == "SOUND" and password == "sound9786":
            request.session["is_admin"] = True
            request.session["admin_username"] = username
            messages.success(request, "Admin login successful!")
            return redirect("admindashboard")
        else:
            messages.error(request, "Invalid admin credentials.")

    return render(request, "admin.html")

# ---------- Admin Dashboard ----------
def admindashboard(request):
    if not request.session.get("is_admin"):
        messages.warning(request, "Admin access required.")
        return redirect("admin_login")

    if request.method == "POST" and request.FILES.get("document"):
        topic = request.POST.get("topic_name", "Python").strip()
        subtopic = request.POST.get("sub_topic_name", "Basics").strip()
        difficulty = request.POST.get("difficulty_level", "medium").strip()
        pdf_file = request.FILES["document"]

        if not pdf_file.name.lower().endswith(".pdf"):
            messages.error(request, "Only PDF files are allowed.")
        elif pdf_file.size > 10 * 1024 * 1024:
            messages.error(request, "File too large. Max 10MB.")
        else:
            try:
                mcqs = extract_mcqs_from_pdf(pdf_file, topic, subtopic, difficulty)
                if not mcqs:
                    from .utils import extract_mcqs_from_pdf_simple_fallback
                    pdf_file.seek(0)
                    mcqs = extract_mcqs_from_pdf_simple_fallback(pdf_file, topic, subtopic, difficulty)

                created_count = 0
                for mcq in mcqs:
                    Mcq.objects.create(
                        topic=topic,
                        subtopic=subtopic,
                        difficulty=difficulty,
                        question_no=mcq.get('question_no'),
                        question=mcq.get('question'),
                        option1=mcq.get('option1'),
                        option2=mcq.get('option2'),
                        option3=mcq.get('option3'),
                        option4=mcq.get('option4'),
                        correct_answer=mcq.get('correct_answer'),
                    )
                    created_count += 1

                messages.success(request, f"Successfully uploaded {created_count} MCQs.")
            except Exception as e:
                logger.error(f"MCQ upload error: {str(e)}")
                messages.error(request, "Error processing PDF.")

    users = Registration.objects.all().order_by("-id")
    form = MCQUploadForm()
    return render(request, "admindashboard.html", {
        "users": users,
        "form": form,
        "admin_username": request.session.get("admin_username", "Admin")
    })

# ---------- Admin Logout ----------
def admin_logout(request):
    request.session.pop("is_admin", None)
    request.session.pop("admin_username", None)
    messages.success(request, "Admin logged out.")
    return redirect("admin_login")

# ---------- Check Session ----------
def check_session(request):
    if request.method == "GET":
        return JsonResponse({
            "is_logged_in": "user_id" in request.session,
            "is_admin": request.session.get("is_admin", False),
            "user_id": request.session.get("user_id"),
            "user_email": request.session.get("user_email"),
            "admin_username": request.session.get("admin_username")
        })
    return JsonResponse({"error": "Method not allowed"}, status=405)

# ---------- Database View ----------
def database_view(request):
    try:
        mcqs = Mcq.objects.all().order_by("-id")[:100]
        total_mcqs = Mcq.objects.count()

        difficulty_stats = {}
        for mcq in Mcq.objects.all():
            diff = mcq.difficulty
            difficulty_stats[diff] = difficulty_stats.get(diff, 0) + 1

    except Exception as e:
        logger.error(f"Database view error: {str(e)}")
        mcqs = []
        total_mcqs = 0
        difficulty_stats = {}
        messages.error(request, "Error loading database.")

    return render(request, "database.html", {
        "mcqs": mcqs,
        "total_mcqs": total_mcqs,
        "difficulty_stats": difficulty_stats
    })

from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def upload_mcq_pdf(request):
    topic = request.POST.get("topic_name", "Python").strip()
    subtopic = request.POST.get("sub_topic_name", "Basics").strip()
    difficulty = request.POST.get("difficulty_level", "medium").strip()
    pdf_file = request.FILES.get("document")

    if not pdf_file or not pdf_file.name.lower().endswith(".pdf"):
        return JsonResponse({"error": "Invalid file type. Only PDF allowed."}, status=400)

    try:
        mcqs = extract_mcqs_from_pdf(pdf_file, topic, subtopic, difficulty)
        for mcq in mcqs:
            Mcq.objects.create(
                topic=topic,
                subtopic=subtopic,
                difficulty=difficulty,
                question_no=mcq.get('question_no'),
                question=mcq.get('question'),
                option1=mcq.get('option1'),
                option2=mcq.get('option2'),
                option3=mcq.get('option3'),
                option4=mcq.get('option4'),
                correct_answer=mcq.get('correct_answer'),
            )
        return redirect("database")  # Replace with your actual URL name
    except Exception as e:
        logger.error(f"upload_mcq_pdf error: {str(e)}")
        return JsonResponse({"error": "Failed to process PDF."}, status=500)


# ---------- Start Quiz ----------
# @login_required
def start_quiz(request):
    if request.method == "POST":
        topic = request.POST.get("topic")
        subtopic = request.POST.get("subtopic")
        difficulty = request.POST.get("difficulty")
        num_questions = int(request.POST.get("num_questions", 5))

        questions = list(Mcq.objects.filter(
            topic=topic,
            subtopic=subtopic,
            difficulty=difficulty
        ))

        if len(questions) < num_questions:
            num_questions = len(questions)

        if not questions:
            messages.warning(request, "No questions available for this selection.")
            return redirect("userdashboard")

        selected_questions = random.sample(questions, num_questions)

        request.session['quiz_questions'] = [q.id for q in selected_questions]
        request.session['quiz_meta'] = {
            "topic": topic,
            "subtopic": subtopic,
            "difficulty": difficulty,
            "num_questions": num_questions,
        }

        context = {
            "questions": selected_questions,
            "num_questions": num_questions,
        }
        return render(request, "quiz.html", context)
    else:
        return redirect("userdashboard")

# ---------- Submit Quiz ----------
# @login_required
def submit_quiz(request):
    if request.method == "POST":
        user = Registration.objects.get(id=request.session["user_id"])

        quiz_question_ids = request.session.get('quiz_questions', [])
        quiz_meta = request.session.get('quiz_meta', {})
        if not quiz_question_ids or not quiz_meta:
            messages.error(request, "Quiz session expired.")
            return redirect("userdashboard")

        questions = Mcq.objects.filter(id__in=quiz_question_ids)

        total_questions = len(quiz_question_ids)
        correct = 0
        wrong = 0

        for q in questions:
            selected = request.POST.get(f"question_{q.id}")
            if selected == q.correct_answer:
                correct += 1
            else:
                wrong += 1

        score = (correct / total_questions) * 100 if total_questions else 0

        QuizResult.objects.create(
            user=user,
            topic=quiz_meta.get("topic", ""),
            subtopic=quiz_meta.get("subtopic", ""),
            difficulty=quiz_meta.get("difficulty", ""),
            date_attempted=timezone.now(),
            total_questions=total_questions,
            correct_questions=correct,
            wrong_questions=wrong,
            score=score,
        )

        request.session.pop('quiz_questions', None)
        request.session.pop('quiz_meta', None)

        return render(request, "result.html", {
            "total": total_questions,
            "correct": correct,
            "wrong": wrong,
            "score": round(score, 2),
        })
    else:
        return redirect("userdashboard")

from django.db.models import Count, Avg

def history(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Please login to view history.")
        return redirect("login")

    quiz_summary = (
        QuizResult.objects.filter(user_id=user_id)
        .values("topic", "subtopic")
        .annotate(
            quizzes_taken=Count("id"),
            avg_score=Avg("score"),
        )
        .order_by("-quizzes_taken")
    )

    return render(request, "history.html", {"quiz_summary": quiz_summary})

def results(request):
    user_id = request.session.get("user_id")
    if not user_id:
        messages.error(request, "Please login to view results.")
        return redirect("login")

    results = QuizResult.objects.filter(user_id=user_id).order_by("-date_attempted")

    return render(request, "results.html", {"results": results})

# views.py - Analytics Dashboard
from django.shortcuts import render, redirect
from django.db.models import Count, Avg, Sum
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import json
from django.urls import reverse


# Import your actual models
from .models import QuizResult, Mcq, Registration


def get_logged_in_user(request):
    """
    Helper to fetch the logged-in user from session
    (since you are using Registration model, not Django's default User).
    """
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    try:
        return Registration.objects.get(id=user_id)
    except Registration.DoesNotExist:
        return None
def login_view(request):
    """
    Custom login view for Registration model.
    """
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            user = Registration.objects.get(username=username, password=password)
            # Save session
            request.session["user_id"] = user.id

            # Handle "next" parameter
            next_url = request.GET.get("next") or reverse("dashboard")
            return redirect(next_url)

        except Registration.DoesNotExist:
            return render(request, "auth/login.html", {"error": "Invalid username or password"})

    return render(request, "auth/login.html")


def logout_view(request):
    """
    Logs out user by clearing session.
    """
    request.session.flush()
    return redirect("login")


def analytics_dashboard(request):
    """
    Main analytics dashboard view with comprehensive quiz analytics
    """
    user = get_logged_in_user(request)
    if not user:
        return redirect("login")  # redirect if not logged in

    # Date range filter (default last 30 days)
    days = int(request.GET.get("days", 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)

    # Basic Statistics
    total_quizzes = QuizResult.objects.filter(user=user).count()
    total_questions = QuizResult.objects.filter(user=user).aggregate(
        total=Sum("total_questions")
    )["total"] or 0

    correct_answers = QuizResult.objects.filter(user=user).aggregate(
        total=Sum("correct_questions")
    )["total"] or 0

    average_score = QuizResult.objects.filter(user=user).aggregate(
        avg=Avg("score")
    )["avg"] or 0

    # Recent Performance
    recent_results = QuizResult.objects.filter(
        user=user, date_attempted__gte=start_date
    ).order_by("-date_attempted")

    recent_quizzes_count = recent_results.count()
    recent_average_score = recent_results.aggregate(avg=Avg("score"))["avg"] or 0

    # Performance by Topic
    topic_performance = (
        QuizResult.objects.filter(user=user)
        .values("topic")
        .annotate(
            count=Count("id"),
            avg_score=Avg("score"),
            total_questions=Sum("total_questions"),
            correct_answers=Sum("correct_questions"),
        )
        .order_by("-avg_score")
    )

    # Performance by Difficulty
    difficulty_performance = (
        QuizResult.objects.filter(user=user)
        .values("difficulty")
        .annotate(
            count=Count("id"),
            avg_score=Avg("score"),
            total_questions=Sum("total_questions"),
            correct_answers=Sum("correct_questions"),
        )
        .order_by("-avg_score")
    )

    # Daily Performance (for chart)
    daily_performance = (
        QuizResult.objects.filter(user=user, date_attempted__gte=start_date)
        .extra(select={"day": "date(date_attempted)"})
        .values("day")
        .annotate(
            quiz_count=Count("id"),
            avg_score=Avg("score"),
            total_correct=Sum("correct_questions"),
            total_questions=Sum("total_questions"),
        )
        .order_by("day")
    )

    chart_dates = [item["day"].strftime("%Y-%m-%d") for item in daily_performance]
    chart_scores = [
        float(item["avg_score"]) if item["avg_score"] else 0 for item in daily_performance
    ]
    chart_quiz_counts = [item["quiz_count"] for item in daily_performance]

    # Best and Worst Topics
    best_topic = topic_performance.first() if topic_performance else None
    worst_topic = topic_performance.last() if topic_performance else None

    # Recent Activity
    recent_activity = QuizResult.objects.filter(user=user).order_by("-date_attempted")[:10]

    context = {
        "total_quizzes": total_quizzes,
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "average_score": round(average_score, 2),
        "accuracy_rate": round(
            (correct_answers / total_questions * 100) if total_questions else 0, 2
        ),
        "recent_quizzes_count": recent_quizzes_count,
        "recent_average_score": round(recent_average_score, 2),
        "days_filter": days,
        "topic_performance": topic_performance,
        "difficulty_performance": difficulty_performance,
        "best_topic": best_topic,
        "worst_topic": worst_topic,
        "recent_activity": recent_activity,
        "chart_dates": json.dumps(chart_dates),
        "chart_scores": json.dumps(chart_scores),
        "chart_quiz_counts": json.dumps(chart_quiz_counts),
    }

    return render(request, "dashboard.html", context)


#ai suggestions
from django.db.models import Count, Avg
from django.shortcuts import render, redirect
from .models import QuizResult, Registration
from .decorators import custom_login_required


def get_enhanced_suggestions(user):
    """
    Generate personalized AI quiz suggestions based on user performance.
    Multiple suggestions will be returned instead of just one.
    """
    difficulty_summary = (
        QuizResult.objects.filter(user=user)
        .values("difficulty")
        .annotate(
            quizzes_taken=Count("id"),
            avg_score=Avg("score"),
        )
    )

    difficulty_stats = {row["difficulty"]: row for row in difficulty_summary}
    suggestions = []

    # ✅ Suggestion 1: Easy → Medium
    if (
        "easy" in difficulty_stats
        and difficulty_stats["easy"]["quizzes_taken"] >= 5
        and difficulty_stats["easy"]["avg_score"] >= 80
    ):
        suggestions.append({
            "title": "Ready for Medium Level!",
            "emoji": "🎯",
            "desc": f"You’ve completed {difficulty_stats['easy']['quizzes_taken']} easy quizzes with "
                    f"{difficulty_stats['easy']['avg_score']:.1f}% accuracy. Time to level up!",
            "action_text": "🚀 Try Medium Quiz",
            "action_url": "/start-quiz/?difficulty=medium",
            "badge": "⬆️ Level Up"
        })

    # ✅ Suggestion 2: Medium → Hard
    if (
        "medium" in difficulty_stats
        and difficulty_stats["medium"]["quizzes_taken"] >= 5
        and difficulty_stats["medium"]["avg_score"] >= 75
    ):
        suggestions.append({
            "title": "Hard Level Unlocked!",
            "emoji": "🔥",
            "desc": f"You’ve mastered medium quizzes with {difficulty_stats['medium']['avg_score']:.1f}% accuracy. "
                    f"Now go for the ultimate challenge!",
            "action_text": "🏆 Try Hard Quiz",
            "action_url": "/start-quiz/?difficulty=hard",
            "badge": "💪 Pro Mode"
        })

    # ✅ Suggestion 3: Hard → New Topic
    if (
        "hard" in difficulty_stats
        and difficulty_stats["hard"]["quizzes_taken"] >= 3
        and difficulty_stats["hard"]["avg_score"] >= 80
    ):
        suggestions.append({
            "title": "Topic Mastery Achieved!",
            "emoji": "🏆",
            "desc": "Amazing! You’ve conquered hard quizzes in this topic. Time to explore a new one!",
            "action_text": "🌟 Explore New Topic",
            "action_url": "/userdashboard/",
            "badge": "🎓 Master"
        })

    # ✅ Suggestion 4: Low accuracy improvement
    if (
        "easy" in difficulty_stats
        and difficulty_stats["easy"]["avg_score"] < 50
    ):
        suggestions.append({
            "title": "Focus on Basics",
            "emoji": "📘",
            "desc": f"Your average score in Easy quizzes is only {difficulty_stats['easy']['avg_score']:.1f}%. "
                    f"Revise fundamentals before moving ahead.",
            "action_text": "📖 Review Easy Quizzes",
            "action_url": "/start-quiz/?difficulty=easy",
            "badge": "🛠 Improve Basics"
        })

    # ✅ Suggestion 5: General motivation (if few quizzes taken)
    total_quizzes = sum(stat["quizzes_taken"] for stat in difficulty_stats.values()) if difficulty_stats else 0
    if total_quizzes < 3:
        suggestions.append({
            "title": "Start Your Journey!",
            "emoji": "🚀",
            "desc": "You haven’t attempted enough quizzes yet. Take more to unlock personalized suggestions!",
            "action_text": "🎯 Take First Quiz",
            "action_url": "/userdashboard/",
            "badge": "🚀 Get Started"
        })

    return suggestions


@custom_login_required
def suggestions_view(request):
    """
    Page to render AI suggestions for the logged-in user
    """
    user = Registration.objects.get(id=request.session["user_id"])
    suggestions = get_enhanced_suggestions(user)

    context = {
        "user": user,
        "suggestions": suggestions,
    }
    return render(request, "suggestions.html", context)
