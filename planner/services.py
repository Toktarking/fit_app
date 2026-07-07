from collections import defaultdict
from datetime import time, timedelta
from itertools import product

from django.db import transaction
from django.utils import timezone

from .models import (
    DayPlan,
    Dish,
    ExtraFoodLog,
    FitnessProfile,
    FitnessProgram,
    MealChoice,
    ProgressCheckIn,
    UserDishPreference,
    UserFoodPreference,
    WeeklyReview,
    WorkoutTemplate,
)


ACTIVITY_MULTIPLIERS = {
    FitnessProfile.ActivityLevel.LOW: 1.2,
    FitnessProfile.ActivityLevel.LIGHT: 1.375,
    FitnessProfile.ActivityLevel.MEDIUM: 1.55,
    FitnessProfile.ActivityLevel.HIGH: 1.725,
}


def calculate_bmr(profile: FitnessProfile) -> float:
    """
    BMR — сколько калорий организм тратит в покое.
    Формула Mifflin-St Jeor.
    """

    weight = profile.weight_kg
    height = profile.height_cm
    age = profile.age

    if profile.gender == FitnessProfile.Gender.MALE:
        return 10 * weight + 6.25 * height - 5 * age + 5

    return 10 * weight + 6.25 * height - 5 * age - 161


def calculate_tdee(profile: FitnessProfile) -> float:
    """
    TDEE — примерный расход калорий с учетом активности.
    """

    bmr = calculate_bmr(profile)
    multiplier = ACTIVITY_MULTIPLIERS.get(profile.activity_level, 1.2)

    return bmr * multiplier


def calculate_daily_calories(profile: FitnessProfile) -> int:
    """
    Рассчитывает целевую дневную калорийность под цель пользователя.

    Важно:
    эта цель — сколько нужно съесть за день.
    Тренировки не прибавляются сверху автоматически, потому что
    активность уже частично учтена через activity_level.
    """

    tdee = calculate_tdee(profile)

    if profile.goal in [
        FitnessProfile.Goal.FAT_LOSS,
        FitnessProfile.Goal.BELLY_FAT_LOSS,
        FitnessProfile.Goal.BODY_RECOMPOSITION,
    ]:
        calories = tdee - 400

    elif profile.goal == FitnessProfile.Goal.MUSCLE_GAIN:
        calories = tdee + 300

    else:
        calories = tdee

    # Защита от слишком жесткой диеты
    if profile.gender == FitnessProfile.Gender.MALE:
        calories = max(calories, 1600)
    else:
        calories = max(calories, 1300)

    return round(calories)


def calculate_daily_protein(profile: FitnessProfile) -> int:
    """
    Белок для похудения + сохранения/роста мышц.
    Примерный ориентир: 1.7–1.9 г на 1 кг веса.
    """

    if profile.goal == FitnessProfile.Goal.MUSCLE_GAIN:
        protein = profile.weight_kg * 1.9
    else:
        protein = profile.weight_kg * 1.8

    return round(protein)


def split_daily_calories(daily_calories: int, meals_per_day: int = 4) -> dict:
    """
    Делит дневные калории на приемы пищи.

    Для MVP используем 3 или 4 приема пищи.
    5 приемов лучше добавить позже отдельной моделью/типом второго перекуса,
    потому что сейчас MealType.SNACK один.
    """

    if meals_per_day == 3:
        return {
            Dish.MealType.BREAKFAST: round(daily_calories * 0.30),
            Dish.MealType.LUNCH: round(daily_calories * 0.40),
            Dish.MealType.DINNER: round(daily_calories * 0.30),
        }

    # Стандартный вариант — 4 приема пищи
    return {
        Dish.MealType.BREAKFAST: round(daily_calories * 0.25),
        Dish.MealType.LUNCH: round(daily_calories * 0.35),
        Dish.MealType.SNACK: round(daily_calories * 0.15),
        Dish.MealType.DINNER: round(daily_calories * 0.25),
    }


def get_excluded_food_ids(user):
    """
    Возвращает продукты, которые пользователь не ест.
    """

    return UserFoodPreference.objects.filter(
        user=user,
        status__in=[
            UserFoodPreference.Status.DISLIKE,
            UserFoodPreference.Status.AVOID,
            UserFoodPreference.Status.ALLERGY,
        ],
    ).values_list("food_id", flat=True)


def get_available_dishes(user, meal_type):
    """
    Возвращает блюда, в которых нет запрещенных продуктов
    и которые пользователь не заблокировал как блюдо.
    """

    excluded_food_ids = get_excluded_food_ids(user)

    excluded_dish_ids = UserDishPreference.objects.filter(
        user=user,
        status__in=[
            UserDishPreference.Status.DISLIKE,
            UserDishPreference.Status.AVOID,
        ],
    ).values_list("dish_id", flat=True)

    return (
        Dish.objects
        .filter(meal_type=meal_type)
        .exclude(id__in=excluded_dish_ids)
        .exclude(ingredients__food_id__in=excluded_food_ids)
        .distinct()
        .order_by("calories", "-protein_g")
    )


def get_meal_options(user, meal_type, target_calories, limit=5):
    """
    Подбирает несколько вариантов блюда под нужный прием пищи и калории.
    Используется на странице выбора блюда.
    """

    min_calories = target_calories - 120
    max_calories = target_calories + 120

    return (
        get_available_dishes(user, meal_type)
        .filter(calories__gte=min_calories, calories__lte=max_calories)
        .order_by("-protein_g", "calories")[:limit]
    )


def get_candidate_dishes_for_meal(user, meal_type, target_calories, limit=20):
    """
    Возвращает кандидаты для автоматического генератора питания.

    Сначала берем блюда в диапазоне target ± 120 ккал.
    Если таких нет, берем ближайшие по калориям блюда этого типа.
    """

    candidates = list(
        get_meal_options(
            user=user,
            meal_type=meal_type,
            target_calories=target_calories,
            limit=limit,
        )
    )

    if candidates:
        return candidates

    available_dishes = list(
        get_available_dishes(
            user=user,
            meal_type=meal_type,
        )
    )

    available_dishes.sort(
        key=lambda dish: abs(dish.calories - target_calories)
    )

    return available_dishes[:limit]


def get_default_meal_times(meals_per_day: int = 4) -> dict:
    """
    Время приемов пищи.
    """

    if meals_per_day == 3:
        return {
            Dish.MealType.BREAKFAST: time(8, 0),
            Dish.MealType.LUNCH: time(14, 0),
            Dish.MealType.DINNER: time(20, 0),
        }

    return {
        Dish.MealType.BREAKFAST: time(8, 0),
        Dish.MealType.LUNCH: time(14, 0),
        Dish.MealType.SNACK: time(17, 0),
        Dish.MealType.DINNER: time(20, 0),
    }


def get_strength_template(day_number: int):
    """
    Чередует силовые тренировки A и B.
    Если шаблонов пока нет, вернет None.
    """

    if day_number % 2 == 0:
        template = WorkoutTemplate.objects.filter(
            workout_type=WorkoutTemplate.WorkoutType.STRENGTH,
            title__icontains="B",
        ).first()
    else:
        template = WorkoutTemplate.objects.filter(
            workout_type=WorkoutTemplate.WorkoutType.STRENGTH,
            title__icontains="A",
        ).first()

    if template:
        return template

    return WorkoutTemplate.objects.filter(
        workout_type=WorkoutTemplate.WorkoutType.STRENGTH,
    ).first()


def get_workout_template_by_type(workout_type):
    return WorkoutTemplate.objects.filter(
        workout_type=workout_type,
    ).first()


def get_day_activities(profile: FitnessProfile, week_number: int, weekday: int):
    """
    Возвращает утреннюю и вечернюю активность.

    weekday:
    0 — понедельник
    1 — вторник
    2 — среда
    3 — четверг
    4 — пятница
    5 — суббота
    6 — воскресенье
    """

    morning_activity = DayPlan.ActivityType.WALK
    evening_activity = DayPlan.ActivityType.REST

    if profile.wants_morning_running:
        if weekday in [0, 2, 4]:
            morning_activity = DayPlan.ActivityType.RUN
        else:
            morning_activity = DayPlan.ActivityType.WALK

    if profile.has_gym and weekday in [0, 2, 4]:
        evening_activity = DayPlan.ActivityType.STRENGTH

    if profile.has_pool:
        if weekday == 1:
            evening_activity = DayPlan.ActivityType.SWIMMING

        if week_number >= 3 and weekday == 5:
            evening_activity = DayPlan.ActivityType.SWIMMING

    if weekday == 3:
        evening_activity = DayPlan.ActivityType.STRETCHING

    if weekday == 6:
        morning_activity = DayPlan.ActivityType.WALK
        evening_activity = DayPlan.ActivityType.REST

    return morning_activity, evening_activity


def get_steps_goal(week_number: int) -> int:
    """
    Постепенно увеличивает цель по шагам.
    """

    if week_number <= 2:
        return 6000

    if week_number <= 4:
        return 7000

    if week_number <= 8:
        return 8000

    return 9000


def get_day_notes(morning_activity, evening_activity, week_number):
    """
    Короткие заметки для пользователя.
    """

    notes = []

    if week_number <= 4:
        notes.append(
            "Месяц 1: адаптация. Главная цель — привыкнуть к режиму без перегруза."
        )
    elif week_number <= 8:
        notes.append(
            "Месяц 2: прогресс. Можно немного увеличивать нагрузку."
        )
    else:
        notes.append(
            "Месяц 3: закрепление. Цель — стабильность и улучшение формы."
        )

    if morning_activity == DayPlan.ActivityType.RUN:
        notes.append("Утром: легкий бег/ходьба, без максимальной скорости.")

    if morning_activity == DayPlan.ActivityType.WALK:
        notes.append("Утром: быстрая ходьба или легкая прогулка.")

    if evening_activity == DayPlan.ActivityType.STRENGTH:
        notes.append("Вечером: силовая тренировка. Главный фокус — техника.")

    if evening_activity == DayPlan.ActivityType.SWIMMING:
        notes.append("Вечером: бассейн в спокойном или среднем темпе.")

    if evening_activity == DayPlan.ActivityType.STRETCHING:
        notes.append("Вечером: растяжка, восстановление, легкая мобилизация.")

    if evening_activity == DayPlan.ActivityType.REST:
        notes.append("Вечером: отдых и восстановление.")

    return "\n".join(notes)


def select_workout_template(evening_activity, day_number):
    """
    Подбирает шаблон тренировки под активность.
    """

    if evening_activity == DayPlan.ActivityType.STRENGTH:
        return get_strength_template(day_number)

    if evening_activity == DayPlan.ActivityType.SWIMMING:
        return get_workout_template_by_type(
            WorkoutTemplate.WorkoutType.SWIMMING
        )

    if evening_activity == DayPlan.ActivityType.STRETCHING:
        return get_workout_template_by_type(
            WorkoutTemplate.WorkoutType.STRETCHING
        )

    return None


def get_morning_duration(morning_activity, week_number):
    """
    Сколько минут делать утреннюю активность.
    """

    if morning_activity == DayPlan.ActivityType.RUN:
        if week_number <= 2:
            return 25
        if week_number <= 4:
            return 30
        if week_number <= 8:
            return 35
        return 40

    if morning_activity == DayPlan.ActivityType.WALK:
        if week_number <= 2:
            return 30
        if week_number <= 8:
            return 35
        return 40

    return 0


def get_evening_duration(evening_activity, week_number):
    """
    Сколько минут делать вечернюю активность.
    """

    if evening_activity == DayPlan.ActivityType.STRENGTH:
        if week_number <= 4:
            return 45
        if week_number <= 8:
            return 50
        return 55

    if evening_activity == DayPlan.ActivityType.SWIMMING:
        if week_number <= 4:
            return 30
        if week_number <= 8:
            return 35
        return 40

    if evening_activity == DayPlan.ActivityType.STRETCHING:
        return 20

    return 0


def get_morning_details(morning_activity, week_number):
    """
    Подробная инструкция для утра.
    """

    if morning_activity == DayPlan.ActivityType.RUN:
        if week_number <= 2:
            return (
                "Бег/ходьба — 25 минут\n"
                "1. 5 минут быстрая ходьба\n"
                "2. 1 минута легкий бег + 2 минуты ходьба — 6 кругов\n"
                "3. 2 минуты спокойная ходьба\n"
                "Темп: легкий, без одышки. Цель — привыкнуть."
            )

        if week_number <= 4:
            return (
                "Бег/ходьба — 30 минут\n"
                "1. 5 минут быстрая ходьба\n"
                "2. 2 минуты легкий бег + 2 минуты ходьба — 6 кругов\n"
                "3. 1 минута спокойная ходьба\n"
                "Темп: можно говорить короткими фразами."
            )

        if week_number <= 8:
            return (
                "Легкий бег — 35 минут\n"
                "1. 5 минут ходьба\n"
                "2. 5 минут легкий бег + 2 минуты ходьба — 4 круга\n"
                "3. 2 минуты спокойная ходьба\n"
                "Не ускоряться. Главная цель — стабильность."
            )

        return (
            "Легкий бег — 40 минут\n"
            "1. 5 минут ходьба\n"
            "2. 10 минут легкий бег + 2 минуты ходьба — 3 круга\n"
            "3. 3–5 минут спокойная ходьба\n"
            "Если тяжело — заменить часть бега ходьбой."
        )

    if morning_activity == DayPlan.ActivityType.WALK:
        if week_number <= 2:
            return (
                "Быстрая ходьба — 30 минут\n"
                "Темп: бодрый, но комфортный.\n"
                "Цель: восстановление после бега/зала и расход калорий."
            )

        if week_number <= 8:
            return (
                "Быстрая ходьба — 35 минут\n"
                "Можно идти на улице или на дорожке.\n"
                "Темп: примерно 5–6 км/ч, если используете дорожку."
            )

        return (
            "Быстрая ходьба — 40 минут\n"
            "Цель: легкое кардио без перегруза суставов."
        )

    return "Утром отдых."


def get_evening_details(evening_activity, week_number):
    """
    Подробная инструкция для вечера.
    """

    if evening_activity == DayPlan.ActivityType.STRENGTH:
        if week_number <= 4:
            return (
                "Силовая тренировка — 45 минут\n"
                "Фокус: техника, легкий/средний вес.\n"
                "Отдых между подходами: 60–90 секунд.\n"
                "Не работать до отказа. Должно оставаться 2–3 повтора в запасе."
            )

        if week_number <= 8:
            return (
                "Силовая тренировка — 50 минут\n"
                "Фокус: постепенное увеличение нагрузки.\n"
                "Если техника хорошая, можно добавить немного вес или 1–2 повтора."
            )

        return (
            "Силовая тренировка — 55 минут\n"
            "Фокус: закрепление формы.\n"
            "Не гнаться за максимальными весами, главное — регулярность и техника."
        )

    if evening_activity == DayPlan.ActivityType.SWIMMING:
        if week_number <= 4:
            return (
                "Бассейн — 30 минут\n"
                "1. 5 минут легкое плавание\n"
                "2. 20 минут спокойное плавание: 1 дорожка + отдых 30–60 секунд\n"
                "3. 5 минут спокойная заминка\n"
                "Цель: восстановление."
            )

        if week_number <= 8:
            return (
                "Бассейн — 35 минут\n"
                "1. 5 минут разминка\n"
                "2. 25 минут: 2 дорожки спокойно + 1 дорожка чуть быстрее\n"
                "3. 5 минут заминка\n"
                "Цель: выносливость и восстановление."
            )

        return (
            "Бассейн — 40 минут\n"
            "1. 5 минут разминка\n"
            "2. 30 минут плавание в среднем темпе\n"
            "3. 5 минут заминка\n"
            "Если усталость высокая — плыть спокойно."
        )

    if evening_activity == DayPlan.ActivityType.STRETCHING:
        return (
            "Растяжка и восстановление — 20 минут\n"
            "1. Растяжка ног — 5 минут\n"
            "2. Растяжка спины — 5 минут\n"
            "3. Легкая мобилизация плеч и таза — 5 минут\n"
            "4. Дыхание/расслабление — 5 минут"
        )

    return "Вечером отдых. Сон и восстановление важны для похудения."


def calculate_activity_calories_burned(
    weight_kg: float,
    activity_type: str,
    duration_minutes: int,
) -> int:
    """
    Примерный расчет сожженных калорий по MET.
    Это не точное значение, а ориентир.
    """

    met_values = {
        DayPlan.ActivityType.WALK: 3.5,
        DayPlan.ActivityType.RUN: 7.0,
        DayPlan.ActivityType.STRENGTH: 5.0,
        DayPlan.ActivityType.SWIMMING: 6.0,
        DayPlan.ActivityType.STRETCHING: 2.5,
        DayPlan.ActivityType.REST: 0,
    }

    met = met_values.get(activity_type, 0)
    calories = met * 3.5 * weight_kg / 200 * duration_minutes

    return round(calories)


@transaction.atomic
def generate_12_week_program(user, start_date=None, overwrite=False):
    """
    Создает 12-недельную программу:
    - калории
    - белок
    - бег/ходьба утром
    - зал
    - бассейн
    - план на каждый день
    """

    profile = FitnessProfile.objects.get(user=user)

    if start_date is None:
        start_date = timezone.localdate()

    daily_calories = calculate_daily_calories(profile)
    daily_protein = calculate_daily_protein(profile)

    profile.daily_calories = daily_calories
    profile.daily_protein_g = daily_protein
    profile.save(update_fields=["daily_calories", "daily_protein_g"])

    if overwrite:
        FitnessProgram.objects.filter(
            user=user,
            is_active=True,
        ).update(is_active=False)

    program = FitnessProgram.objects.create(
        user=user,
        title="12 недель — убрать живот и войти в форму",
        duration_weeks=12,
        start_date=start_date,
        daily_calories=daily_calories,
        daily_protein_g=daily_protein,
        is_active=True,
    )

    total_days = 12 * 7

    for day_index in range(total_days):
        current_date = start_date + timedelta(days=day_index)
        week_number = day_index // 7 + 1
        day_number = day_index + 1
        weekday = current_date.weekday()

        morning_activity, evening_activity = get_day_activities(
            profile=profile,
            week_number=week_number,
            weekday=weekday,
        )

        workout_template = select_workout_template(
            evening_activity=evening_activity,
            day_number=day_number,
        )

        morning_duration = get_morning_duration(
            morning_activity,
            week_number,
        )

        evening_duration = get_evening_duration(
            evening_activity,
            week_number,
        )

        morning_calories_burned = calculate_activity_calories_burned(
            weight_kg=profile.weight_kg,
            activity_type=morning_activity,
            duration_minutes=morning_duration,
        )

        evening_calories_burned = calculate_activity_calories_burned(
            weight_kg=profile.weight_kg,
            activity_type=evening_activity,
            duration_minutes=evening_duration,
        )

        DayPlan.objects.create(
            program=program,
            week_number=week_number,
            day_number=day_number,
            date=current_date,
            calories_goal=daily_calories,
            protein_goal_g=daily_protein,
            steps_goal=get_steps_goal(week_number),
            morning_activity=morning_activity,
            evening_activity=evening_activity,
            morning_duration_minutes=morning_duration,
            evening_duration_minutes=evening_duration,
            morning_calories_burned=morning_calories_burned,
            evening_calories_burned=evening_calories_burned,
            morning_details=get_morning_details(
                morning_activity,
                week_number,
            ),
            evening_details=get_evening_details(
                evening_activity,
                week_number,
            ),
            workout_template=workout_template,
            notes=get_day_notes(
                morning_activity,
                evening_activity,
                week_number,
            ),
        )

    return program

def generate_meal_choices_for_day(day_plan: DayPlan, replace_existing=False):
    """
    Генерирует питание на день так, чтобы:
    1. сумма калорий была близка к цели дня;
    2. блюда не повторялись каждый день, если есть другие варианты.
    """

    user = day_plan.program.user
    profile = FitnessProfile.objects.get(user=user)

    if day_plan.meals.exists() and not replace_existing:
        return list(day_plan.meals.select_related("dish").all())

    if replace_existing:
        day_plan.meals.all().delete()

    calorie_split = split_daily_calories(
        daily_calories=day_plan.calories_goal,
        meals_per_day=profile.meals_per_day,
    )

    meal_times = get_default_meal_times(profile.meals_per_day)
    meal_types = list(calorie_split.keys())

    candidates_by_meal_type = {}

    for meal_type in meal_types:
        target_calories = calorie_split[meal_type]

        candidates = get_candidate_dishes_for_meal(
            user=user,
            meal_type=meal_type,
            target_calories=target_calories,
            limit=20,
        )

        if not candidates:
            return []

        candidates_by_meal_type[meal_type] = candidates

    used_dish_ids = set(
        MealChoice.objects.filter(
            day_plan__program=day_plan.program,
            day_plan__week_number=day_plan.week_number,
        )
        .exclude(day_plan=day_plan)
        .values_list("dish_id", flat=True)
    )

    used_dish_ids_by_meal_type = defaultdict(set)

    used_meals = (
        MealChoice.objects.filter(
            day_plan__program=day_plan.program,
            day_plan__week_number=day_plan.week_number,
        )
        .exclude(day_plan=day_plan)
        .values_list("meal_type", "dish_id")
    )

    for meal_type, dish_id in used_meals:
        used_dish_ids_by_meal_type[meal_type].add(dish_id)

    candidate_lists = [
        candidates_by_meal_type[meal_type]
        for meal_type in meal_types
    ]

    best_combo = None
    best_score = None

    for combo in product(*candidate_lists):
        total_calories = sum(dish.calories for dish in combo)
        total_protein = sum(dish.protein_g for dish in combo)

        difference = abs(total_calories - day_plan.calories_goal)
        is_over_goal = total_calories > day_plan.calories_goal

        repeated_dishes_count = sum(
            1 for dish in combo if dish.id in used_dish_ids
        )

        repeated_same_meal_type_count = sum(
            1
            for meal_type, dish in zip(meal_types, combo)
            if dish.id in used_dish_ids_by_meal_type[meal_type]
        )

        """
        Логика score:
        1. Если разница в пределах 80 ккал — считаем это нормальным.
        2. Среди нормальных вариантов выбираем тот, где меньше повторов.
        3. Потом смотрим точность по калориям.
        4. Потом предпочитаем вариант без перебора.
        5. Потом больше белка.
        """

        score = (
            max(0, difference - 80),
            repeated_same_meal_type_count,
            repeated_dishes_count,
            difference,
            is_over_goal,
            -total_protein,
        )

        if best_score is None or score < best_score:
            best_score = score
            best_combo = combo

    if not best_combo:
        return []

    created_meals = []

    for meal_type, dish in zip(meal_types, best_combo):
        meal = MealChoice.objects.create(
            day_plan=day_plan,
            meal_type=meal_type,
            dish=dish,
            meal_time=meal_times.get(meal_type),
        )

        created_meals.append(meal)

    return created_meals

def generate_meal_choices_for_week(
    program: FitnessProgram,
    week_number: int,
    replace_existing=False,
):
    """
    Генерирует питание на конкретную неделю.

    Если replace_existing=True, сначала удаляет питание всей недели,
    а потом генерирует заново. Это нужно, чтобы старые блюда не мешали
    логике разнообразия.
    """

    day_plans = program.day_plans.filter(
        week_number=week_number,
    ).order_by("date")

    if replace_existing:
        MealChoice.objects.filter(
            day_plan__in=day_plans,
        ).delete()

    result = []

    for day_plan in day_plans:
        meals = generate_meal_choices_for_day(
            day_plan=day_plan,
            replace_existing=False,
        )
        result.extend(meals)

    return result

def generate_meal_choices_for_program(
    program: FitnessProgram,
    replace_existing=False,
):
    """
    Генерирует питание на все 12 недель.
    """

    result = []

    for day_plan in program.day_plans.all().order_by("date"):
        meals = generate_meal_choices_for_day(
            day_plan=day_plan,
            replace_existing=replace_existing,
        )
        result.extend(meals)

    return result


def generate_shopping_list_for_program(
    program: FitnessProgram,
    week_number=None,
):
    """
    Формирует список покупок на программу или конкретную неделю.
    """

    meal_choices = MealChoice.objects.filter(
        day_plan__program=program,
    )

    if week_number is not None:
        meal_choices = meal_choices.filter(
            day_plan__week_number=week_number,
        )

    meal_choices = meal_choices.select_related("dish").prefetch_related(
        "dish__ingredients__food"
    )

    shopping = defaultdict(lambda: {"grams": 0, "category": ""})

    for meal_choice in meal_choices:
        for ingredient in meal_choice.dish.ingredients.all():
            food = ingredient.food

            shopping[food.name]["grams"] += ingredient.grams
            shopping[food.name]["category"] = food.get_category_display()

    return dict(shopping)


def format_shopping_list(shopping_list: dict) -> str:
    """
    Превращает список покупок в красивый текст.
    """

    grouped = defaultdict(list)

    for food_name, data in shopping_list.items():
        category = data["category"]
        grams = data["grams"]

        if grams >= 1000:
            amount = f"{round(grams / 1000, 2)} кг"
        else:
            amount = f"{grams} г"

        grouped[category].append(f"- {food_name}: {amount}")

    lines = []

    for category, items in grouped.items():
        lines.append(category)
        lines.extend(items)
        lines.append("")

    return "\n".join(lines)


def generate_weekly_review(
    program: FitnessProgram,
    week_number: int,
) -> WeeklyReview:
    """
    Анализирует неделю и создает рекомендацию:
    - менять ли калории
    - менять ли шаги
    - продолжать ли текущий план
    """

    day_plans = program.day_plans.filter(
        week_number=week_number,
    ).order_by("date")

    if not day_plans.exists():
        raise ValueError("Такой недели в программе нет.")

    start_date = day_plans.first().date
    end_date = day_plans.last().date

    checkins = ProgressCheckIn.objects.filter(
        user=program.user,
        date__gte=start_date,
        date__lte=end_date,
    ).order_by("date")

    extra_foods = ExtraFoodLog.objects.filter(
        day_plan__program=program,
        day_plan__week_number=week_number,
    )

    total_extra_calories = sum(
        item.calories for item in extra_foods
    )

    extra_food_days = (
        extra_foods
        .values("day_plan_id")
        .distinct()
        .count()
    )

    avg_extra_calories = round(total_extra_calories / 7, 1)

    total_tasks = 0
    completed_tasks = 0

    completed_morning_count = 0
    completed_evening_count = 0

    total_meals_count = 0
    completed_meals_count = 0

    for day in day_plans:
        if day.morning_duration_minutes > 0:
            total_tasks += 1

            if day.morning_completed:
                completed_tasks += 1
                completed_morning_count += 1

        if (
            day.evening_duration_minutes > 0
            and day.evening_activity != DayPlan.ActivityType.REST
        ):
            total_tasks += 1

            if day.evening_completed:
                completed_tasks += 1
                completed_evening_count += 1

        meals = day.meals.all()

        for meal in meals:
            total_tasks += 1
            total_meals_count += 1

            if meal.is_completed:
                completed_tasks += 1
                completed_meals_count += 1

    if total_tasks > 0:
        completion_percent = round(completed_tasks / total_tasks * 100)
    else:
        completion_percent = 0

    start_weight = None
    end_weight = None
    weight_change = None

    start_waist = None
    end_waist = None
    waist_change = None

    avg_energy = None
    avg_hunger = None

    if checkins.exists():
        first_checkin = checkins.first()
        last_checkin = checkins.last()

        start_weight = first_checkin.weight_kg
        end_weight = last_checkin.weight_kg
        weight_change = round(end_weight - start_weight, 2)

        if first_checkin.waist_cm and last_checkin.waist_cm:
            start_waist = first_checkin.waist_cm
            end_waist = last_checkin.waist_cm
            waist_change = round(end_waist - start_waist, 2)

        energy_values = [
            item.energy_level for item in checkins
        ]

        hunger_values = [
            item.hunger_level for item in checkins
        ]

        avg_energy = round(
            sum(energy_values) / len(energy_values),
            1,
        )

        avg_hunger = round(
            sum(hunger_values) / len(hunger_values),
            1,
        )

    calorie_adjustment = 0
    steps_adjustment = 0
    recommendation_parts = []

    recommendation_parts.append(
        f"Выполнение плана за неделю: {completion_percent}%."
    )

    if total_extra_calories > 0:
        recommendation_parts.append(
            f"Дополнительно за неделю съедено примерно {total_extra_calories} ккал. "
            f"В среднем это {avg_extra_calories} ккал в день."
        )

    if checkins.count() < 2:
        recommendation_parts.append(
            "Недостаточно ежедневных отчетов. Для точной корректировки нужно хотя бы 2 записи веса за неделю."
        )
        recommendation_parts.append(
            "Пока лучше не менять калории. Сначала заполняйте ежедневный отчет и отмечайте выполнение."
        )

    else:
        if weight_change is not None:
            if weight_change <= -1.0:
                calorie_adjustment = 100
                recommendation_parts.append(
                    "Вес снизился слишком быстро. Лучше добавить примерно 100 ккал, чтобы не терять силы и не сорваться."
                )

            elif -1.0 < weight_change <= -0.3:
                recommendation_parts.append(
                    "Вес снижается нормальным темпом. Калории менять не нужно."
                )

            elif weight_change > -0.3:
                if waist_change is not None and waist_change <= -1.0:
                    recommendation_parts.append(
                        "Вес почти не изменился, но талия уменьшилась. Это хороший знак, можно продолжать текущий план."
                    )

                elif completion_percent < 70:
                    recommendation_parts.append(
                        "Вес и талия почти не меняются, но выполнение плана ниже 70%. "
                        "Сначала нужно улучшить регулярность, а не снижать калории."
                    )

                else:
                    if avg_extra_calories >= 150:
                        recommendation_parts.append(
                            "Вес и талия почти не меняются, но есть дополнительные калории вне плана. "
                            "Сначала лучше уменьшить незапланированные перекусы, а не снижать базовый рацион."
                        )
                    else:
                        calorie_adjustment = -100
                        steps_adjustment = 1000
                        recommendation_parts.append(
                            "Вес и талия почти не меняются, а выполнение плана нормальное. "
                            "Можно снизить калории на 100 ккал и добавить 1000 шагов в день."
                        )

        if avg_energy is not None and avg_energy <= 3:
            if calorie_adjustment < 0:
                calorie_adjustment = 0

            recommendation_parts.append(
                "Энергия низкая. Не стоит дополнительно снижать калории на следующей неделе."
            )

        if avg_hunger is not None and avg_hunger >= 8:
            if calorie_adjustment < 0:
                calorie_adjustment = 0

            recommendation_parts.append(
                "Голод высокий. Лучше добавить больше белка, овощей и не снижать калории."
            )

    recommendation = "\n".join(recommendation_parts)

    review, _ = WeeklyReview.objects.update_or_create(
        program=program,
        week_number=week_number,
        defaults={
            "start_date": start_date,
            "end_date": end_date,
            "start_weight_kg": start_weight,
            "end_weight_kg": end_weight,
            "weight_change_kg": weight_change,
            "start_waist_cm": start_waist,
            "end_waist_cm": end_waist,
            "waist_change_cm": waist_change,
            "avg_energy_level": avg_energy,
            "avg_hunger_level": avg_hunger,
            "completed_morning_count": completed_morning_count,
            "completed_evening_count": completed_evening_count,
            "total_meals_count": total_meals_count,
            "completed_meals_count": completed_meals_count,
            "completion_percent": completion_percent,
            "calorie_adjustment": calorie_adjustment,
            "steps_adjustment": steps_adjustment,
            "recommendation": recommendation,
            "total_extra_calories": total_extra_calories,
            "avg_extra_calories": avg_extra_calories,
            "extra_food_days": extra_food_days,
        },
    )

    return review


def apply_weekly_review(review: WeeklyReview):
    """
    Применяет корректировку к следующим неделям программы.
    Например:
    - минус 100 ккал
    - плюс 1000 шагов
    """

    if review.is_applied:
        return review

    program = review.program
    profile = FitnessProfile.objects.get(user=program.user)

    if profile.gender == FitnessProfile.Gender.MALE:
        min_calories = 1600
    else:
        min_calories = 1300

    future_days = program.day_plans.filter(
        week_number__gt=review.week_number,
    )

    for day in future_days:
        new_calories = day.calories_goal + review.calorie_adjustment
        new_calories = max(new_calories, min_calories)

        new_steps = day.steps_goal + review.steps_adjustment
        new_steps = max(new_steps, 4000)
        new_steps = min(new_steps, 12000)

        day.calories_goal = new_calories
        day.steps_goal = new_steps
        day.save(update_fields=["calories_goal", "steps_goal"])

    new_program_calories = (
        program.daily_calories + review.calorie_adjustment
    )

    new_program_calories = max(new_program_calories, min_calories)

    program.daily_calories = new_program_calories
    program.save(update_fields=["daily_calories"])

    profile.daily_calories = new_program_calories
    profile.save(update_fields=["daily_calories"])

    review.is_applied = True
    review.save(update_fields=["is_applied"])

    return review
