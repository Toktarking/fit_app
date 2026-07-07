from django.conf import settings
from django.db import models


class FitnessProfile(models.Model):



    class Gender(models.TextChoices):
        MALE = "male", "Мужчина"
        FEMALE = "female", "Женщина"

    class Goal(models.TextChoices):
        FAT_LOSS = "fat_loss", "Похудеть"
        BELLY_FAT_LOSS = "belly_fat_loss", "Убрать живот"
        BODY_RECOMPOSITION = "body_recomposition", "Похудеть и подкачаться"
        MUSCLE_GAIN = "muscle_gain", "Набрать мышечную массу"
        MAINTAIN = "maintain", "Поддерживать форму"

    class ActivityLevel(models.TextChoices):
        LOW = "low", "Низкая активность"
        LIGHT = "light", "Легкая активность"
        MEDIUM = "medium", "Средняя активность"
        HIGH = "high", "Высокая активность"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fitness_profile",
    )

    gender = models.CharField(max_length=20, choices=Gender.choices)
    age = models.PositiveIntegerField()
    height_cm = models.PositiveIntegerField()
    weight_kg = models.FloatField()

    goal = models.CharField(max_length=40, choices=Goal.choices)
    activity_level = models.CharField(
        max_length=20,
        choices=ActivityLevel.choices,
        default=ActivityLevel.LOW,
    )

    has_gym = models.BooleanField(default=False)
    wants_morning_running = models.BooleanField(default=True)
    has_pool = models.BooleanField(default=False)

    meals_per_day = models.PositiveIntegerField(default=4)

    timezone = models.CharField(
        max_length=64,
        default="Asia/Almaty",
        help_text="Часовой пояс пользователя",
    )


    daily_calories = models.PositiveIntegerField(null=True, blank=True)
    daily_protein_g = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Профиль: {self.user}"


class Food(models.Model):
    class Category(models.TextChoices):
        PROTEIN = "protein", "Белок"
        CARB = "carb", "Углеводы"
        FAT = "fat", "Жиры"
        VEGETABLE = "vegetable", "Овощи"
        FRUIT = "fruit", "Фрукты"
        DAIRY = "dairy", "Молочные продукты"
        DRINK = "drink", "Напитки"
        OTHER = "other", "Другое"

    name = models.CharField(max_length=120)
    category = models.CharField(max_length=30, choices=Category.choices)

    calories_per_100g = models.PositiveIntegerField()
    protein_per_100g = models.FloatField(default=0)
    fat_per_100g = models.FloatField(default=0)
    carbs_per_100g = models.FloatField(default=0)

    is_common = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class UserFoodPreference(models.Model):
    class Status(models.TextChoices):
        LIKE = "like", "Ем"
        DISLIKE = "dislike", "Не люблю"
        AVOID = "avoid", "Не ем"
        ALLERGY = "allergy", "Аллергия"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="food_preferences",
    )
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices)

    class Meta:
        unique_together = ("user", "food")

    def __str__(self):
        return f"{self.user} — {self.food}: {self.get_status_display()}"


class Dish(models.Model):
    class MealType(models.TextChoices):
        BREAKFAST = "breakfast", "Завтрак"
        LUNCH = "lunch", "Обед"
        SNACK = "snack", "Полдник"
        DINNER = "dinner", "Ужин"

    title = models.CharField(max_length=150)
    meal_type = models.CharField(max_length=30, choices=MealType.choices)

    calories = models.PositiveIntegerField()
    protein_g = models.FloatField(default=0)
    fat_g = models.FloatField(default=0)
    carbs_g = models.FloatField(default=0)
    

    cooking_time_minutes = models.PositiveIntegerField(default=15)
    
    description = models.TextField(blank=True)
    cooking_steps = models.TextField(blank=True)

    def __str__(self):
        return self.title



class UserDishPreference(models.Model):
    class Status(models.TextChoices):
        DISLIKE = "dislike", "Не нравится"
        AVOID = "avoid", "Не показывать"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dish_preferences",
    )
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "dish")

    def __str__(self):
        return f"{self.user} — {self.dish}: {self.get_status_display()}"

class DishIngredient(models.Model):
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        related_name="ingredients",
    )
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    grams = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.dish} — {self.food} {self.grams} г"


class Exercise(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Легко"
        MEDIUM = "medium", "Средне"
        HARD = "hard", "Сложно"

    name = models.CharField(max_length=120)
    muscle_group = models.CharField(max_length=100)
    difficulty = models.CharField(
        max_length=20,
        choices=Difficulty.choices,
        default=Difficulty.EASY,
    )
    equipment = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class WorkoutTemplate(models.Model):
    class WorkoutType(models.TextChoices):
        STRENGTH = "strength", "Силовая"
        RUNNING = "running", "Бег"
        WALKING = "walking", "Ходьба"
        SWIMMING = "swimming", "Бассейн"
        STRETCHING = "stretching", "Растяжка"

    title = models.CharField(max_length=150)
    workout_type = models.CharField(max_length=30, choices=WorkoutType.choices)
    duration_minutes = models.PositiveIntegerField(default=30)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class WorkoutTemplateExercise(models.Model):
    workout_template = models.ForeignKey(
        WorkoutTemplate,
        on_delete=models.CASCADE,
        related_name="exercises",
    )
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)

    sets = models.PositiveIntegerField(default=3)
    reps = models.CharField(max_length=30, default="10")
    rest_seconds = models.PositiveIntegerField(default=60)
    estimated_minutes = models.PositiveIntegerField(default=5)

    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.workout_template} — {self.exercise}"


class FitnessProgram(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fitness_programs",
    )

    title = models.CharField(max_length=150, default="12 недель — убрать живот и войти в форму")
    duration_weeks = models.PositiveIntegerField(default=12)

    start_date = models.DateField()
    daily_calories = models.PositiveIntegerField()
    daily_protein_g = models.PositiveIntegerField()

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class DayPlan(models.Model):
    class ActivityType(models.TextChoices):
        RUN = "run", "Бег"
        WALK = "walk", "Ходьба"
        STRENGTH = "strength", "Силовая"
        SWIMMING = "swimming", "Бассейн"
        REST = "rest", "Отдых"
        STRETCHING = "stretching", "Растяжка"

    program = models.ForeignKey(
        FitnessProgram,
        on_delete=models.CASCADE,
        related_name="day_plans",
    )

    week_number = models.PositiveIntegerField()
    day_number = models.PositiveIntegerField()
    date = models.DateField()

    calories_goal = models.PositiveIntegerField()
    protein_goal_g = models.PositiveIntegerField()
    steps_goal = models.PositiveIntegerField(default=7000)

    morning_activity = models.CharField(
        max_length=30,
        choices=ActivityType.choices,
        default=ActivityType.WALK,
    )
    evening_activity = models.CharField(
        max_length=30,
        choices=ActivityType.choices,
        default=ActivityType.REST,
    )

    morning_completed = models.BooleanField(default=False)
    evening_completed = models.BooleanField(default=False)


    morning_duration_minutes = models.PositiveIntegerField(default=30)
    evening_duration_minutes = models.PositiveIntegerField(default=0)

    morning_details = models.TextField(blank=True)
    evening_details = models.TextField(blank=True)

    morning_calories_burned = models.PositiveIntegerField(default=0)
    evening_calories_burned = models.PositiveIntegerField(default=0)




    workout_template = models.ForeignKey(
        WorkoutTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["date"]

    @property
    def total_calories_burned(self):
        return self.morning_calories_burned + self.evening_calories_burned

    def __str__(self):
        return f"День {self.day_number}, неделя {self.week_number}"


class MealChoice(models.Model):
    day_plan = models.ForeignKey(
        DayPlan,
        on_delete=models.CASCADE,
        related_name="meals",
    )

    meal_type = models.CharField(max_length=30, choices=Dish.MealType.choices)
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    meal_time = models.TimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.day_plan} — {self.get_meal_type_display()} — {self.dish}"


class ExtraFoodLog(models.Model):
    day_plan = models.ForeignKey(
        DayPlan,
        on_delete=models.CASCADE,
        related_name="extra_foods",
    )

    title = models.CharField(max_length=150)
    calories = models.PositiveIntegerField()

    protein_g = models.FloatField(default=0, blank=True)
    fat_g = models.FloatField(default=0, blank=True)
    carbs_g = models.FloatField(default=0, blank=True)

    quantity_description = models.CharField(
        max_length=150,
        blank=True,
        help_text="Например: 1 шоколадка, 2 печенья, 1 стакан сока",
    )

    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.title} — {self.calories} ккал"

class ProgressCheckIn(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="progress_checkins",
    )

    date = models.DateField()
    weight_kg = models.FloatField()
    waist_cm = models.FloatField(null=True, blank=True)

    completed_workouts = models.PositiveIntegerField(default=0)
    completed_morning_activities = models.PositiveIntegerField(default=0)

    energy_level = models.PositiveIntegerField(default=5)
    hunger_level = models.PositiveIntegerField(default=5)

    comment = models.TextField(blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user} — {self.date} — {self.weight_kg} кг"

class WeeklyReview(models.Model):
    program = models.ForeignKey(
        FitnessProgram,
        on_delete=models.CASCADE,
        related_name="weekly_reviews",
    )

    week_number = models.PositiveIntegerField()

    start_date = models.DateField()
    end_date = models.DateField()

    start_weight_kg = models.FloatField(null=True, blank=True)
    end_weight_kg = models.FloatField(null=True, blank=True)
    weight_change_kg = models.FloatField(null=True, blank=True)

    start_waist_cm = models.FloatField(null=True, blank=True)
    end_waist_cm = models.FloatField(null=True, blank=True)
    waist_change_cm = models.FloatField(null=True, blank=True)

    avg_energy_level = models.FloatField(null=True, blank=True)
    avg_hunger_level = models.FloatField(null=True, blank=True)

    completed_morning_count = models.PositiveIntegerField(default=0)
    completed_evening_count = models.PositiveIntegerField(default=0)

    total_meals_count = models.PositiveIntegerField(default=0)
    completed_meals_count = models.PositiveIntegerField(default=0)


    total_extra_calories = models.PositiveIntegerField(default=0)
    avg_extra_calories = models.FloatField(default=0)
    extra_food_days = models.PositiveIntegerField(default=0)


    completion_percent = models.PositiveIntegerField(default=0)

    calorie_adjustment = models.IntegerField(default=0)
    steps_adjustment = models.IntegerField(default=0)

    recommendation = models.TextField(blank=True)

    is_applied = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("program", "week_number")
        ordering = ["week_number"]

    def __str__(self):
        return f"{self.program} — неделя {self.week_number}"
        



class WorkoutSession(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "В процессе"
        FINISHED = "finished", "Завершена"

    day_plan = models.OneToOneField(
        DayPlan,
        on_delete=models.CASCADE,
        related_name="workout_session",
    )

    workout_template = models.ForeignKey(
        WorkoutTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Тренировка: {self.day_plan.date} — {self.get_status_display()}"

    @property
    def is_finished(self):
        return self.status == self.Status.FINISHED

    @property
    def total_exercises_count(self):
        return self.session_exercises.count()

    @property
    def completed_exercises_count(self):
        return self.session_exercises.filter(is_completed=True).count()

    @property
    def remaining_exercises_count(self):
        return self.total_exercises_count - self.completed_exercises_count

    @property
    def completion_percent(self):
        total = self.total_exercises_count

        if total == 0:
            return 0

        return round(self.completed_exercises_count / total * 100)

    @property
    def can_finish(self):
        return (
            self.total_exercises_count > 0
            and self.completed_exercises_count == self.total_exercises_count
        )


class WorkoutSessionExercise(models.Model):
    session = models.ForeignKey(
        WorkoutSession,
        on_delete=models.CASCADE,
        related_name="session_exercises",
    )

    template_exercise = models.ForeignKey(
        WorkoutTemplateExercise,
        on_delete=models.CASCADE,
    )

    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.template_exercise.exercise.name



class NotificationLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_logs",
    )
    date = models.DateField()
    notification_key = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "date", "notification_key")
        ordering = ["-sent_at"]

    def __str__(self):
        return f"{self.user} — {self.date} — {self.notification_key}"
        