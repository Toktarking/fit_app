from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import time

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

from webpush import send_user_notification

from .forms import FitnessProfileForm, ProgressCheckInForm, ExtraFoodLogForm
from .models import (
    DayPlan,
    Dish,
    ExtraFoodLog,
    FitnessProfile,
    FitnessProgram,
    Food,
    MealChoice,
    ProgressCheckIn,
    UserDishPreference,
    UserFoodPreference,
    WeeklyReview,
    WorkoutSession,
    WorkoutSessionExercise,
)
from .services import (
    apply_weekly_review,
    calculate_daily_calories,
    calculate_daily_protein,
    format_shopping_list,
    generate_12_week_program,
    generate_meal_choices_for_week,
    generate_shopping_list_for_program,
    generate_weekly_review,
    get_default_meal_times,
    get_meal_options,
    split_daily_calories,
)

@login_required
def dashboard(request):
    context = get_today_context(request)
    return render(request, "planner/dashboard.html", context)


@login_required
def today_section(request, section):
    allowed_sections = [
        "morning",
        "nutrition",
        "evening",
        "extra",
        "checkin",
    ]

    if section not in allowed_sections:
        messages.warning(request, "Такой раздел не найден.")
        return redirect("planner:dashboard")

    context = get_today_context(request)
    context["section"] = section

    if not context["program"]:
        messages.warning(request, "Сначала создайте фитнес-программу.")
        return redirect("planner:dashboard")

    if not context["day_plan"]:
        messages.warning(request, "На сегодня пока нет плана.")
        return redirect("planner:dashboard")

    return render(request, "planner/today_section.html", context)

@login_required
def profile_form(request):
    profile = FitnessProfile.objects.filter(user=request.user).first()

    if request.method == "POST":
        form = FitnessProfileForm(request.POST, instance=profile)

        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user

            profile.daily_calories = calculate_daily_calories(profile)
            profile.daily_protein_g = calculate_daily_protein(profile)

            profile.save()

            messages.success(request, "Анкета сохранена.")
            return redirect("planner:dashboard")
    else:
        form = FitnessProfileForm(instance=profile)

    context = {
        "form": form,
    }

    return render(request, "planner/profile_form.html", context)


@login_required
def create_program(request):
    profile = FitnessProfile.objects.filter(user=request.user).first()

    if not profile:
        messages.warning(request, "Сначала заполните анкету.")
        return redirect("planner:profile_form")

    program = generate_12_week_program(
        user=request.user,
        start_date=timezone.localdate(),
        overwrite=True,
    )

    generate_meal_choices_for_week(
        program=program,
        week_number=1,
        replace_existing=True,
    )

    messages.success(request, "Программа на 12 недель создана.")
    return redirect("planner:today")


def build_daily_schedule(day_plan, meals, checkin):
    """
    Собирает расписание дня:
    - утро
    - приемы пищи
    - вечерняя тренировка
    - ежедневный отчет
    """

    if not day_plan:
        return []

    schedule = []

    def add_item(
        time_value,
        title,
        description,
        section,
        status_text="",
        status_class="",
        meal_id=None,
        is_completed=False,
    ):
        schedule.append(
            {
                "time": time_value,
                "title": title,
                "description": description,
                "section": section,
                "status_text": status_text,
                "status_class": status_class,
                "meal_id": meal_id,
                "is_completed": is_completed,
            }
        )

    # Утро
    if day_plan.morning_duration_minutes > 0:
        if day_plan.morning_completed:
            status_text = "✅ выполнено"
            status_class = "status-done"
        else:
            status_text = "⏳ запланировано"
            status_class = "status-pending"

        add_item(
            time_value=time(7, 30),
            title="Утро",
            description=(
                f"{day_plan.get_morning_activity_display()} — "
                f"{day_plan.morning_duration_minutes} мин., "
                f"≈ {day_plan.morning_calories_burned} ккал"
            ),
            section="morning",
            status_text=status_text,
            status_class=status_class,
            is_completed=day_plan.morning_completed,
        )

    # Питание
    for meal in meals:
        if meal.is_completed:
            status_text = "✅ съедено"
            status_class = "status-done"
        else:
            status_text = "⏳ нужно съесть"
            status_class = "status-pending"

        meal_time = meal.meal_time

        if not meal_time:
            if meal.meal_type == Dish.MealType.BREAKFAST:
                meal_time = time(8, 30)
            elif meal.meal_type == Dish.MealType.LUNCH:
                meal_time = time(13, 30)
            elif meal.meal_type == Dish.MealType.SNACK:
                meal_time = time(17, 0)
            elif meal.meal_type == Dish.MealType.DINNER:
                meal_time = time(20, 30)
            else:
                meal_time = time(12, 0)



        add_item(
            time_value=meal_time,
            title=meal.get_meal_type_display(),
            description=(
                f"{meal.dish.title} — "
                f"{meal.dish.calories} ккал"
            ),
            section="nutrition",
            status_text=status_text,
            status_class=status_class,
            meal_id=meal.id,
            is_completed=meal.is_completed,
        )

    # Вечерняя активность
    if (
        day_plan.evening_duration_minutes > 0
        and day_plan.evening_activity != DayPlan.ActivityType.REST
    ):
        if day_plan.evening_completed:
            status_text = "✅ выполнено"
            status_class = "status-done"
        else:
            status_text = "⏳ запланировано"
            status_class = "status-pending"

        add_item(
            time_value=time(19, 0),
            title="Вечер",
            description=(
                f"{day_plan.get_evening_activity_display()} — "
                f"{day_plan.evening_duration_minutes} мин., "
                f"≈ {day_plan.evening_calories_burned} ккал"
            ),
            section="evening",
            status_text=status_text,
            status_class=status_class,
            is_completed=day_plan.evening_completed,
        )

    # Ежедневный отчет
    if checkin:
        status_text = "✅ заполнен"
        status_class = "status-done"
    else:
        status_text = "⏳ нужно заполнить"
        status_class = "status-pending"

    add_item(
        time_value=time(21, 30),
        title="Ежедневный отчет",
        description="Вес, талия, энергия, голод и комментарий за день",
        section="checkin",
        status_text=status_text,
        status_class=status_class,
        is_completed=bool(checkin),
    )

    return sorted(schedule, key=lambda item: item["time"])


def get_today_context(request):
    profile = FitnessProfile.objects.filter(user=request.user).first()

    program = FitnessProgram.objects.filter(
        user=request.user,
        is_active=True,
    ).first()

    today_plan = None
    meals = []
    extra_foods = []
    checkin = None

    planned_meal_calories = 0
    completed_meal_calories = 0
    extra_calories = 0
    total_eaten_calories = 0
    remaining_calories = 0
    over_calories = 0
    total_calories_burned = 0

    total_tasks = 0
    completed_tasks = 0
    completion_percent = 0
    daily_schedule = []

    if program:
        today_plan = DayPlan.objects.filter(
            program=program,
            date=timezone.localdate(),
        ).first()

        if not today_plan:
            today_plan = program.day_plans.order_by("date").first()

    if today_plan:
        meals = today_plan.meals.select_related("dish").all()
        extra_foods = today_plan.extra_foods.all()

        planned_meal_calories = sum(
            meal.dish.calories for meal in meals
        )

        completed_meal_calories = sum(
            meal.dish.calories for meal in meals if meal.is_completed
        )

        extra_calories = sum(
            item.calories for item in extra_foods
        )

        total_eaten_calories = completed_meal_calories + extra_calories
        remaining_calories = today_plan.calories_goal - total_eaten_calories

        if remaining_calories < 0:
            over_calories = abs(remaining_calories)

        total_calories_burned = (
            today_plan.morning_calories_burned
            + today_plan.evening_calories_burned
        )

        checkin = ProgressCheckIn.objects.filter(
            user=request.user,
            date=today_plan.date,
        ).first()

        daily_schedule = build_daily_schedule(
            day_plan=today_plan,
            meals=meals,
            checkin=checkin,
        )

        if today_plan.morning_duration_minutes > 0:
            total_tasks += 1
            if today_plan.morning_completed:
                completed_tasks += 1

        if (
            today_plan.evening_duration_minutes > 0
            and today_plan.evening_activity != DayPlan.ActivityType.REST
        ):
            total_tasks += 1
            if today_plan.evening_completed:
                completed_tasks += 1

        for meal in meals:
            total_tasks += 1
            if meal.is_completed:
                completed_tasks += 1

        if total_tasks > 0:
            completion_percent = round(completed_tasks / total_tasks * 100)

    return {
        "profile": profile,
        "program": program,
        "day_plan": today_plan,
        "meals": meals,
        "extra_foods": extra_foods,
        "checkin": checkin,
        "planned_meal_calories": planned_meal_calories,
        "completed_meal_calories": completed_meal_calories,
        "extra_calories": extra_calories,
        "total_eaten_calories": total_eaten_calories,
        "remaining_calories": remaining_calories,
        "over_calories": over_calories,
        "total_calories_burned": total_calories_burned,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_percent": completion_percent,
        "daily_schedule": daily_schedule,
    }



@login_required
def today(request):
    program = FitnessProgram.objects.filter(
        user=request.user,
        is_active=True,
    ).first()

    if not program:
        messages.warning(
            request,
            "У вас пока нет активной программы. Сначала создайте программу на 12 недель.",
        )
        return redirect("planner:dashboard")

    today_plan = DayPlan.objects.filter(
        program=program,
        date=timezone.localdate(),
    ).first()

    if not today_plan:
        today_plan = program.day_plans.order_by("date").first()

    if not today_plan:
        messages.warning(
            request,
            "Программа создана, но в ней пока нет дней. Попробуйте создать программу заново.",
        )
        return redirect("planner:dashboard")

    meals = today_plan.meals.select_related("dish").all()
    extra_foods = today_plan.extra_foods.all()

    planned_meal_calories = sum(
        meal.dish.calories for meal in meals
    )

    completed_meal_calories = sum(
        meal.dish.calories for meal in meals if meal.is_completed
    )

    extra_calories = sum(
        item.calories for item in extra_foods
    )

    total_eaten_calories = completed_meal_calories + extra_calories
    remaining_calories = today_plan.calories_goal - total_eaten_calories

    over_calories = 0

    if remaining_calories < 0:
        over_calories = abs(remaining_calories)

    total_calories_burned = (
        today_plan.morning_calories_burned
        + today_plan.evening_calories_burned
    )

    checkin = ProgressCheckIn.objects.filter(
        user=request.user,
        date=today_plan.date,
    ).first()

    total_tasks = 0
    completed_tasks = 0

    if today_plan.morning_duration_minutes > 0:
        total_tasks += 1

        if today_plan.morning_completed:
            completed_tasks += 1

    if (
        today_plan.evening_duration_minutes > 0
        and today_plan.evening_activity != DayPlan.ActivityType.REST
    ):
        total_tasks += 1

        if today_plan.evening_completed:
            completed_tasks += 1

    for meal in meals:
        total_tasks += 1

        if meal.is_completed:
            completed_tasks += 1

    if total_tasks > 0:
        completion_percent = round(completed_tasks / total_tasks * 100)
    else:
        completion_percent = 0

    context = {
        "program": program,
        "day_plan": today_plan,
        "meals": meals,
        "checkin": checkin,

        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_percent": completion_percent,

        "extra_foods": extra_foods,

        "planned_meal_calories": planned_meal_calories,
        "completed_meal_calories": completed_meal_calories,
        "extra_calories": extra_calories,
        "total_eaten_calories": total_eaten_calories,
        "remaining_calories": remaining_calories,
        "over_calories": over_calories,

        "total_calories_burned": total_calories_burned,
    }

    return render(request, "planner/today.html", context)

@login_required
def week_view(request, week_number):
    program = FitnessProgram.objects.filter(
        user=request.user,
        is_active=True,
    ).first()

    if not program:
        messages.warning(request, "Сначала создайте фитнес-программу.")
        return redirect("planner:dashboard")

    day_plans = (
        program.day_plans
        .filter(week_number=week_number)
        .prefetch_related("meals__dish", "extra_foods")
        .order_by("date")
    )

    for day in day_plans:
        meals = day.meals.all()
        extra_foods = day.extra_foods.all()

        meal_calories_total = sum(
            meal.dish.calories for meal in meals
        )

        completed_meal_calories_total = sum(
            meal.dish.calories for meal in meals if meal.is_completed
        )

        extra_calories_total = sum(
            extra_food.calories for extra_food in extra_foods
        )

        total_calories_with_extra = (
            meal_calories_total + extra_calories_total
        )

        total_eaten_calories = (
            completed_meal_calories_total + extra_calories_total
        )

        calories_difference = (
            total_calories_with_extra - day.calories_goal
        )

        total_calories_burned = (
            day.morning_calories_burned
            + day.evening_calories_burned
        )

        net_calories_after_activity = (
            total_calories_with_extra - total_calories_burned
        )

        net_difference = (
            net_calories_after_activity - day.calories_goal
        )

        day.meal_calories_total = meal_calories_total
        day.completed_meal_calories_total = completed_meal_calories_total
        day.extra_calories_total = extra_calories_total

        day.total_calories_with_extra = total_calories_with_extra
        day.total_eaten_calories = total_eaten_calories

        day.calories_difference = calories_difference
        day.calories_abs_difference = abs(calories_difference)

        day.net_calories_after_activity = net_calories_after_activity
        day.net_difference = net_difference
        day.net_abs_difference = abs(net_difference)

    context = {
        "program": program,
        "week_number": week_number,
        "day_plans": day_plans,
    }

    return render(request, "planner/week.html", context)

@login_required
def generate_week_meals(request, week_number):
    program = get_object_or_404(
        FitnessProgram,
        user=request.user,
        is_active=True,
    )

    generate_meal_choices_for_week(
        program=program,
        week_number=week_number,
        replace_existing=True,
    )

    messages.success(request, f"Питание на неделю {week_number} обновлено.")
    return redirect("planner:week", week_number=week_number)


@login_required
def meal_options(request, day_plan_id, meal_type):
    day_plan = get_object_or_404(
        DayPlan,
        id=day_plan_id,
        program__user=request.user,
    )

    profile = get_object_or_404(
        FitnessProfile,
        user=request.user,
    )

    calorie_split = split_daily_calories(
        day_plan.calories_goal,
        profile.meals_per_day,
    )

    target_calories = calorie_split.get(meal_type)

    if target_calories is None:
        messages.warning(request, "Такой прием пищи не найден.")
        return redirect("planner:today")

    options = get_meal_options(
        user=request.user,
        meal_type=meal_type,
        target_calories=target_calories,
        limit=10,
    )

    current_meal = MealChoice.objects.filter(
        day_plan=day_plan,
        meal_type=meal_type,
    ).first()

    context = {
        "day_plan": day_plan,
        "meal_type": meal_type,
        "meal_type_display": dict(Dish.MealType.choices).get(meal_type),
        "options": options,
        "current_meal": current_meal,
        "target_calories": target_calories,
    }

    return render(request, "planner/meal_options.html", context)


@login_required
def choose_dish(request, day_plan_id, meal_type, dish_id):
    day_plan = get_object_or_404(
        DayPlan,
        id=day_plan_id,
        program__user=request.user,
    )

    dish = get_object_or_404(
        Dish,
        id=dish_id,
        meal_type=meal_type,
    )

    profile = FitnessProfile.objects.filter(
        user=request.user,
    ).first()

    meal_time = None

    if profile:
        meal_times = get_default_meal_times(profile.meals_per_day)
        meal_time = meal_times.get(meal_type)

    MealChoice.objects.update_or_create(
        day_plan=day_plan,
        meal_type=meal_type,
        defaults={
            "dish": dish,
            "meal_time": meal_time,
        },
    )

    messages.success(request, "Блюдо выбрано.")
    return redirect("planner:today")


@login_required
def shopping_list(request, week_number):
    program = get_object_or_404(
        FitnessProgram,
        user=request.user,
        is_active=True,
    )

    shopping = generate_shopping_list_for_program(
        program=program,
        week_number=week_number,
    )

    shopping_text = format_shopping_list(shopping)

    context = {
        "program": program,
        "week_number": week_number,
        "shopping": shopping,
        "shopping_text": shopping_text,
    }

    return render(request, "planner/shopping_list.html", context)


@login_required
def food_preferences(request):
    foods = Food.objects.all().order_by("category", "name")

    existing_preferences = {
        preference.food_id: preference.status
        for preference in UserFoodPreference.objects.filter(user=request.user)
    }

    if request.method == "POST":
        for food in foods:
            status = request.POST.get(f"food_{food.id}", "not_set")

            if status == "not_set":
                UserFoodPreference.objects.filter(
                    user=request.user,
                    food=food,
                ).delete()

            elif status in [
                UserFoodPreference.Status.LIKE,
                UserFoodPreference.Status.DISLIKE,
                UserFoodPreference.Status.AVOID,
                UserFoodPreference.Status.ALLERGY,
            ]:
                UserFoodPreference.objects.update_or_create(
                    user=request.user,
                    food=food,
                    defaults={
                        "status": status,
                    },
                )

        messages.success(request, "Предпочтения по продуктам сохранены.")

        action = request.POST.get("action")

        if action == "save_and_regenerate":
            program = FitnessProgram.objects.filter(
                user=request.user,
                is_active=True,
            ).first()

            if program:
                today_plan = DayPlan.objects.filter(
                    program=program,
                    date=timezone.localdate(),
                ).first()

                if today_plan:
                    current_week_number = today_plan.week_number
                else:
                    current_week_number = 1

                generate_meal_choices_for_week(
                    program=program,
                    week_number=current_week_number,
                    replace_existing=True,
                )

                messages.success(
                    request,
                    f"Питание на неделю {current_week_number} обновлено с учетом предпочтений.",
                )

                return redirect(
                    "planner:week",
                    week_number=current_week_number,
                )

        return redirect("planner:food_preferences")

    grouped_foods = defaultdict(list)

    for food in foods:
        food.current_status = existing_preferences.get(food.id, "not_set")
        grouped_foods[food.get_category_display()].append(food)

    context = {
        "grouped_foods": dict(grouped_foods),
        "status_choices": UserFoodPreference.Status.choices,
    }

    return render(request, "planner/food_preferences.html", context)


@login_required
def dish_feedback(request, day_plan_id, meal_type, dish_id):
    day_plan = get_object_or_404(
        DayPlan,
        id=day_plan_id,
        program__user=request.user,
    )

    dish = get_object_or_404(
        Dish.objects.prefetch_related("ingredients__food"),
        id=dish_id,
    )

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "avoid_dish":
            UserDishPreference.objects.update_or_create(
                user=request.user,
                dish=dish,
                defaults={
                    "status": UserDishPreference.Status.AVOID,
                },
            )

            MealChoice.objects.filter(
                day_plan=day_plan,
                meal_type=meal_type,
                dish=dish,
            ).delete()

            messages.success(
                request,
                "Это блюдо больше не будет предлагаться.",
            )

            return redirect(
                "planner:meal_options",
                day_plan_id=day_plan.id,
                meal_type=meal_type,
            )

        if action == "avoid_food":
            food_id = request.POST.get("food_id")
            status = request.POST.get(
                "status",
                UserFoodPreference.Status.AVOID,
            )

            allowed_statuses = [
                UserFoodPreference.Status.DISLIKE,
                UserFoodPreference.Status.AVOID,
                UserFoodPreference.Status.ALLERGY,
            ]

            if status not in allowed_statuses:
                status = UserFoodPreference.Status.AVOID

            food = get_object_or_404(Food, id=food_id)

            UserFoodPreference.objects.update_or_create(
                user=request.user,
                food=food,
                defaults={
                    "status": status,
                },
            )

            MealChoice.objects.filter(
                day_plan=day_plan,
                meal_type=meal_type,
                dish=dish,
            ).delete()

            messages.success(
                request,
                f"Продукт “{food.name}” сохранен как неподходящий. "
                "Блюда с ним больше не будут предлагаться.",
            )

            return redirect(
                "planner:meal_options",
                day_plan_id=day_plan.id,
                meal_type=meal_type,
            )

        messages.warning(request, "Выберите, что именно не подходит.")

    context = {
        "day_plan": day_plan,
        "meal_type": meal_type,
        "meal_type_display": dict(Dish.MealType.choices).get(meal_type),
        "dish": dish,
    }

    return render(request, "planner/dish_feedback.html", context)


@login_required
@require_POST
def toggle_morning_completed(request, day_plan_id):
    day_plan = get_object_or_404(
        DayPlan,
        id=day_plan_id,
        program__user=request.user,
    )

    day_plan.morning_completed = not day_plan.morning_completed
    day_plan.save(update_fields=["morning_completed"])

    next_url = request.POST.get("next")

    if next_url:
        return redirect(next_url)

    return redirect("planner:today")


@login_required
@require_POST
def toggle_evening_completed(request, day_plan_id):
    day_plan = get_object_or_404(
        DayPlan,
        id=day_plan_id,
        program__user=request.user,
    )

    day_plan.evening_completed = not day_plan.evening_completed
    day_plan.save(update_fields=["evening_completed"])

    next_url = request.POST.get("next")

    if next_url:
        return redirect(next_url)

    return redirect("planner:today")


@login_required
@require_POST
def toggle_meal_completed(request, meal_id):
    meal = get_object_or_404(
        MealChoice,
        id=meal_id,
        day_plan__program__user=request.user,
    )

    meal.is_completed = not meal.is_completed
    meal.save(update_fields=["is_completed"])

    next_url = request.POST.get("next")

    if next_url:
        return redirect(next_url)

    return redirect("planner:today")


@login_required
def daily_checkin(request, day_plan_id):
    day_plan = get_object_or_404(
        DayPlan,
        id=day_plan_id,
        program__user=request.user,
    )

    checkin = ProgressCheckIn.objects.filter(
        user=request.user,
        date=day_plan.date,
    ).first()

    if request.method == "POST":
        form = ProgressCheckInForm(request.POST, instance=checkin)

        if form.is_valid():
            checkin = form.save(commit=False)
            checkin.user = request.user
            checkin.date = day_plan.date

            if day_plan.morning_completed:
                checkin.completed_morning_activities = 1
            else:
                checkin.completed_morning_activities = 0

            if (
                day_plan.evening_completed
                and day_plan.evening_activity != DayPlan.ActivityType.REST
            ):
                checkin.completed_workouts = 1
            else:
                checkin.completed_workouts = 0

            checkin.save()

            messages.success(request, "Ежедневный отчет сохранен.")
            return redirect("planner:today")
    else:
        form = ProgressCheckInForm(instance=checkin)

    context = {
        "form": form,
        "day_plan": day_plan,
        "checkin": checkin,
    }

    return render(request, "planner/daily_checkin.html", context)


@login_required
def progress_history(request):
    checkins = ProgressCheckIn.objects.filter(
        user=request.user,
    ).order_by("-date")[:30]

    context = {
        "checkins": checkins,
    }

    return render(request, "planner/progress_history.html", context)


@login_required
def weekly_review(request, week_number):
    program = get_object_or_404(
        FitnessProgram,
        user=request.user,
        is_active=True,
    )

    review = generate_weekly_review(
        program=program,
        week_number=week_number,
    )

    context = {
        "program": program,
        "review": review,
        "week_number": week_number,
    }

    return render(request, "planner/weekly_review.html", context)


@login_required
@require_POST
def apply_review(request, week_number):
    program = get_object_or_404(
        FitnessProgram,
        user=request.user,
        is_active=True,
    )

    review = get_object_or_404(
        WeeklyReview,
        program=program,
        week_number=week_number,
    )

    apply_weekly_review(review)

    for next_week_number in range(
        week_number + 1,
        program.duration_weeks + 1,
    ):
        generate_meal_choices_for_week(
            program=program,
            week_number=next_week_number,
            replace_existing=True,
        )

    messages.success(
        request,
        f"Корректировка после недели {week_number} применена к следующим неделям.",
    )

    return redirect("planner:weekly_review", week_number=week_number)


@login_required
def add_extra_food(request, day_plan_id):
    day_plan = get_object_or_404(
        DayPlan,
        id=day_plan_id,
        program__user=request.user,
    )

    if request.method == "POST":
        form = ExtraFoodLogForm(request.POST)

        if form.is_valid():
            extra_food = form.save(commit=False)
            extra_food.day_plan = day_plan
            extra_food.save()

            messages.success(request, "Дополнительная еда добавлена.")
            return redirect("planner:today")
    else:
        form = ExtraFoodLogForm()

    context = {
        "form": form,
        "day_plan": day_plan,
    }

    return render(request, "planner/extra_food_form.html", context)


@login_required
@require_POST
def delete_extra_food(request, extra_food_id):
    extra_food = get_object_or_404(
        ExtraFoodLog,
        id=extra_food_id,
        day_plan__program__user=request.user,
    )

    extra_food.delete()

    messages.success(request, "Запись удалена.")
    return redirect("planner:today")


@login_required
def dish_detail(request, dish_id):
    dish = get_object_or_404(
        Dish.objects.prefetch_related("ingredients__food"),
        id=dish_id,
    )

    context = {
        "dish": dish,
    }

    return render(request, "planner/dish_detail.html", context)


@login_required
def start_workout_session(request, day_plan_id):
    day_plan = get_object_or_404(
        DayPlan,
        id=day_plan_id,
        program__user=request.user,
    )

    if not day_plan.workout_template:
        messages.warning(request, "Для этого дня нет шаблона тренировки.")
        return redirect("planner:today")

    session, created = WorkoutSession.objects.get_or_create(
        day_plan=day_plan,
        defaults={
            "workout_template": day_plan.workout_template,
            "status": WorkoutSession.Status.IN_PROGRESS,
        },
    )

    if created:
        template_exercises = (
            day_plan.workout_template.exercises
            .select_related("exercise")
            .order_by("order")
        )

        for item in template_exercises:
            WorkoutSessionExercise.objects.create(
                session=session,
                template_exercise=item,
                order=item.order,
            )

    if session.status == WorkoutSession.Status.FINISHED:
        messages.info(request, "Эта тренировка уже завершена.")
        return redirect("planner:today")

    return redirect("planner:workout_session", session_id=session.id)


@login_required
def workout_session(request, session_id):
    session = get_object_or_404(
        WorkoutSession.objects.select_related(
            "day_plan",
            "workout_template",
            "day_plan__program",
        ).prefetch_related(
            "session_exercises__template_exercise__exercise",
        ),
        id=session_id,
        day_plan__program__user=request.user,
    )

    context = {
        "session": session,
        "day_plan": session.day_plan,
        "session_exercises": session.session_exercises.all(),
    }

    return render(request, "planner/workout_session.html", context)


@require_POST
@login_required
def toggle_workout_exercise(request, session_exercise_id):
    session_exercise = get_object_or_404(
        WorkoutSessionExercise,
        id=session_exercise_id,
        session__day_plan__program__user=request.user,
    )

    if session_exercise.session.status == WorkoutSession.Status.FINISHED:
        messages.warning(request, "Тренировка уже завершена.")
        return redirect(
            "planner:workout_session",
            session_id=session_exercise.session.id,
        )

    session_exercise.is_completed = not session_exercise.is_completed

    if session_exercise.is_completed:
        session_exercise.completed_at = timezone.now()
    else:
        session_exercise.completed_at = None

    session_exercise.save(
        update_fields=[
            "is_completed",
            "completed_at",
        ]
    )

    return redirect(
        "planner:workout_session",
        session_id=session_exercise.session.id,
    )
@require_POST
@login_required
def finish_workout_session(request, session_id):
    session = get_object_or_404(
        WorkoutSession,
        id=session_id,
        day_plan__program__user=request.user,
    )

    if session.status == WorkoutSession.Status.FINISHED:
        return redirect("planner:today")

    total_exercises = session.session_exercises.count()

    completed_exercises = session.session_exercises.filter(
        is_completed=True,
    ).count()

    if total_exercises == 0:
        messages.warning(
            request,
            "В этой тренировке нет упражнений. Завершить тренировку нельзя.",
        )
        return redirect("planner:today")

    if completed_exercises < total_exercises:
        messages.warning(
            request,
            f"Тренировка еще не завершена: выполнено {completed_exercises} из {total_exercises} упражнений. "
            "Вы можете продолжить тренировку позже.",
        )

        return redirect("planner:today")

    session.status = WorkoutSession.Status.FINISHED
    session.finished_at = timezone.now()
    session.save(update_fields=["status", "finished_at"])

    day_plan = session.day_plan
    day_plan.evening_completed = True
    day_plan.save(update_fields=["evening_completed"])

    messages.success(request, "Тренировка завершена. Отличная работа!")
    return redirect("planner:today")

@login_required
def today_meal_detail(request, meal_id):
    meal = get_object_or_404(
        MealChoice.objects.select_related(
            "dish",
            "day_plan",
            "day_plan__program",
        ).prefetch_related(
            "dish__ingredients__food",
        ),
        id=meal_id,
        day_plan__program__user=request.user,
    )

    day_plan = meal.day_plan
    dish = meal.dish

    context = {
        "meal": meal,
        "day_plan": day_plan,
        "dish": dish,
    }

    return render(request, "planner/today_meal_detail.html", context)


def register(request):
    if request.user.is_authenticated:
        return redirect("planner:dashboard")

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Аккаунт создан. Теперь заполните профиль.")
            return redirect("planner:profile_form")
    else:
        form = UserCreationForm()

    return render(request, "planner/register.html", {"form": form})


@require_POST
@login_required
def send_test_push(request):
    payload = {
        "head": "Уведомления работают",
        "body": "Это тестовое уведомление от фитнес-приложения.",
        "url": "/",
    }

    try:
        send_user_notification(
            user=request.user,
            payload=payload,
            ttl=1000,
        )
        messages.success(request, "Тестовое уведомление отправлено.")
    except Exception as error:
        messages.error(request, f"Не удалось отправить уведомление: {error}")

    return redirect("planner:dashboard")
