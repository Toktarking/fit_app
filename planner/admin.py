from django.contrib import admin

from .models import (
    Food,
    Dish,
    DishIngredient,
    Exercise,
    WorkoutTemplate,
    WorkoutTemplateExercise,
    FitnessProfile,
    FitnessProgram,
    DayPlan,
    MealChoice,
    ProgressCheckIn,
    UserFoodPreference,
    UserDishPreference,
    ExtraFoodLog,
    WeeklyReview,
    WorkoutSession,
    WorkoutSessionExercise,
)


class DishIngredientInline(admin.TabularInline):
    model = DishIngredient
    extra = 1


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ("title", "meal_type", "calories", "protein_g", "cooking_time_minutes")
    list_filter = ("meal_type",)
    search_fields = ("title",)
    inlines = [DishIngredientInline]


class WorkoutTemplateExerciseInline(admin.TabularInline):
    model = WorkoutTemplateExercise
    extra = 1


@admin.register(WorkoutTemplate)
class WorkoutTemplateAdmin(admin.ModelAdmin):
    list_display = ("title", "workout_type", "duration_minutes")
    list_filter = ("workout_type",)
    search_fields = ("title",)
    inlines = [WorkoutTemplateExerciseInline]


@admin.register(FitnessProfile)
class FitnessProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "gender",
        "age",
        "height_cm",
        "weight_kg",
        "goal",
        "has_gym",
        "has_pool",
        "meals_per_day",
    )


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "calories_per_100g",
        "protein_per_100g",
        "fat_per_100g",
        "carbs_per_100g",
    )
    list_filter = ("category",)
    search_fields = ("name",)


@admin.register(UserFoodPreference)
class UserFoodPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "food", "status")
    list_filter = ("status",)


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "muscle_group", "difficulty", "equipment")
    list_filter = ("muscle_group", "difficulty")
    search_fields = ("name",)


@admin.register(FitnessProgram)
class FitnessProgramAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "duration_weeks", "start_date", "daily_calories", "daily_protein_g", "is_active")


@admin.register(DayPlan)
class DayPlanAdmin(admin.ModelAdmin):
    list_display = (
        "program",
        "week_number",
        "day_number",
        "date",
        "calories_goal",
        "morning_activity",
        "evening_activity",
    )
    list_filter = ("week_number", "morning_activity", "evening_activity")


@admin.register(MealChoice)
class MealChoiceAdmin(admin.ModelAdmin):
    list_display = ("day_plan", "meal_type", "dish", "meal_time")
    list_filter = ("meal_type",)


@admin.register(ProgressCheckIn)
class ProgressCheckInAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "date",
        "weight_kg",
        "waist_cm",
        "completed_workouts",
        "completed_morning_activities",
    )

@admin.register(UserDishPreference)
class UserDishPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "dish", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("dish__title", "user__username")

@admin.register(WeeklyReview)
class WeeklyReviewAdmin(admin.ModelAdmin):
    list_display = (
        "program",
        "week_number",
        "start_date",
        "end_date",
        "weight_change_kg",
        "waist_change_cm",
        "completion_percent",
        "calorie_adjustment",
        "steps_adjustment",
        "is_applied",
    )
    list_filter = ("week_number", "is_applied")

@admin.register(ExtraFoodLog)
class ExtraFoodLogAdmin(admin.ModelAdmin):
    list_display = (
        "day_plan",
        "title",
        "calories",
        "quantity_description",
        "created_at",
    )
    search_fields = ("title", "note")


class WorkoutSessionExerciseInline(admin.TabularInline):
    model = WorkoutSessionExercise
    extra = 0


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = (
        "day_plan",
        "workout_template",
        "status",
        "started_at",
        "finished_at",
    )
    list_filter = ("status",)
    inlines = [WorkoutSessionExerciseInline]