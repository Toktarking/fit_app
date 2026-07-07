from django.urls import path

from . import views

app_name = "planner"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("profile/", views.profile_form, name="profile_form"),
    path("food-preferences/", views.food_preferences, name="food_preferences"),

    path("program/create/", views.create_program, name="create_program"),
    path("today/", views.today, name="today"),

    path(
        "day/<int:day_plan_id>/checkin/",
        views.daily_checkin,
        name="daily_checkin",
    ),
    path(
        "progress/",
        views.progress_history,
        name="progress_history",
    ),

    path("week/<int:week_number>/", views.week_view, name="week"),
    path("week/<int:week_number>/generate-meals/", views.generate_week_meals, name="generate_week_meals"),
    path("shopping/<int:week_number>/", views.shopping_list, name="shopping_list"),

    path(
        "week/<int:week_number>/review/",
        views.weekly_review,
        name="weekly_review",
    ),
    path(
        "week/<int:week_number>/review/apply/",
        views.apply_review,
        name="apply_review",
    ),

    path(
        "day/<int:day_plan_id>/extra-food/add/",
        views.add_extra_food,
        name="add_extra_food",
    ),
    path(
        "extra-food/<int:extra_food_id>/delete/",
        views.delete_extra_food,
        name="delete_extra_food",
    ),
    path("dish/<int:dish_id>/", views.dish_detail, name="dish_detail"),


    path(
        "day/<int:day_plan_id>/toggle-morning/",
        views.toggle_morning_completed,
        name="toggle_morning_completed",
    ),
    path(
        "day/<int:day_plan_id>/toggle-evening/",
        views.toggle_evening_completed,
        name="toggle_evening_completed",
    ),
    path(
        "meal/<int:meal_id>/toggle/",
        views.toggle_meal_completed,
        name="toggle_meal_completed",
    ),

    path(
        "day/<int:day_plan_id>/meal/<str:meal_type>/options/",
        views.meal_options,
        name="meal_options",
    ),
    path(
        "day/<int:day_plan_id>/meal/<str:meal_type>/choose/<int:dish_id>/",
        views.choose_dish,
        name="choose_dish",
    ),
    path(
        "day/<int:day_plan_id>/meal/<str:meal_type>/dish/<int:dish_id>/feedback/",
        views.dish_feedback,
        name="dish_feedback",
    ),

    path(
        "today/section/<str:section>/",
        views.today_section,
        name="today_section",
    ),

    path(
        "today/meal/<int:meal_id>/",
        views.today_meal_detail,
        name="today_meal_detail",
    ),





    path(
        "day/<int:day_plan_id>/workout/start/",
        views.start_workout_session,
        name="start_workout_session",
    ),

    path(
        "workout-session/<int:session_id>/",
        views.workout_session,
        name="workout_session",
    ),

    path(
        "workout-exercise/<int:session_exercise_id>/toggle/",
        views.toggle_workout_exercise,
        name="toggle_workout_exercise",
    ),

    path(
        "workout-session/<int:session_id>/finish/",
        views.finish_workout_session,
        name="finish_workout_session",
    ),


    path(
        "notifications/test/",
        views.send_test_push,
        name="send_test_push",
    ),


]