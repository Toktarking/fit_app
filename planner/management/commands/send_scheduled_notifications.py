from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from webpush import send_user_notification

from planner.models import (
    DayPlan,
    Dish,
    FitnessProgram,
    FitnessProfile,
    MealChoice,
    NotificationLog,
    ProgressCheckIn,
)


def get_user_timezone(user):
    profile = FitnessProfile.objects.filter(user=user).first()

    if not profile or not profile.timezone:
        return ZoneInfo("Asia/Almaty")

    try:
        return ZoneInfo(profile.timezone)
    except ZoneInfoNotFoundError:
        return ZoneInfo("Asia/Almaty")


def get_fallback_meal_time(meal_type):
    if meal_type == Dish.MealType.BREAKFAST:
        return time(8, 0)

    if meal_type == Dish.MealType.LUNCH:
        return time(14, 0)

    if meal_type == Dish.MealType.SNACK:
        return time(17, 0)

    if meal_type == Dish.MealType.DINNER:
        return time(20, 0)

    return time(12, 0)


def build_notification_items(user, day_plan):
    items = []

    if day_plan.morning_duration_minutes > 0:
        items.append(
            {
                "key": "morning",
                "time": time(7, 30),
                "completed": day_plan.morning_completed,
                "title": "Пора выполнить утреннюю активность",
                "body": (
                    f"{day_plan.get_morning_activity_display()} — "
                    f"{day_plan.morning_duration_minutes} мин."
                ),
                "url": "/today/section/morning/",
            }
        )

    meals = day_plan.meals.select_related("dish").order_by("meal_time", "id")

    for meal in meals:
        meal_time = meal.meal_time or get_fallback_meal_time(meal.meal_type)

        items.append(
            {
                "key": f"meal:{meal.meal_type}",
                "time": meal_time,
                "completed": meal.is_completed,
                "title": f"Пора: {meal.get_meal_type_display()}",
                "body": f"{meal.dish.title} — {meal.dish.calories} ккал",
                "url": f"/today/meal/{meal.id}/",
            }
        )

    if (
        day_plan.evening_duration_minutes > 0
        and day_plan.evening_activity != DayPlan.ActivityType.REST
    ):
        items.append(
            {
                "key": "evening",
                "time": time(19, 0),
                "completed": day_plan.evening_completed,
                "title": "Пора выполнить вечернюю активность",
                "body": (
                    f"{day_plan.get_evening_activity_display()} — "
                    f"{day_plan.evening_duration_minutes} мин."
                ),
                "url": "/today/section/evening/",
            }
        )

    checkin_exists = ProgressCheckIn.objects.filter(
        user=user,
        date=day_plan.date,
    ).exists()

    items.append(
        {
            "key": "checkin",
            "time": time(21, 30),
            "completed": checkin_exists,
            "title": "Заполните ежедневный отчет",
            "body": "Укажите вес, талию, уровень энергии, голода и комментарий за день.",
            "url": "/today/section/checkin/",
        }
    )

    return items


class Command(BaseCommand):
    help = "Send scheduled push notifications for today's fitness plan using each user's timezone."

    def add_arguments(self, parser):
        parser.add_argument(
            "--window-minutes",
            type=int,
            default=10,
        )

        parser.add_argument(
            "--force",
            action="store_true",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
        )

        parser.add_argument(
            "--username",
            type=str,
            default=None,
        )

        parser.add_argument(
            "--key",
            type=str,
            default=None,
        )

    def handle(self, *args, **options):
        window_minutes = options["window_minutes"]

        User = get_user_model()
        users = User.objects.filter(is_active=True)

        if options["username"]:
            users = users.filter(username=options["username"])

        sent_count = 0
        skipped_count = 0

        for user in users:
            user_tz = get_user_timezone(user)
            user_now = timezone.now().astimezone(user_tz)
            user_today = user_now.date()

            program = FitnessProgram.objects.filter(
                user=user,
                is_active=True,
            ).first()

            if not program:
                continue

            day_plan = DayPlan.objects.filter(
                program=program,
                date=user_today,
            ).first()

            if not day_plan:
                continue

            items = build_notification_items(user, day_plan)

            for item in items:
                if options["key"] and item["key"] != options["key"]:
                    continue

                if item["completed"]:
                    skipped_count += 1
                    continue

                scheduled_datetime = datetime.combine(
                    user_today,
                    item["time"],
                    tzinfo=user_tz,
                )

                send_until = scheduled_datetime + timedelta(minutes=window_minutes)

                is_due = scheduled_datetime <= user_now <= send_until

                if options["force"]:
                    is_due = True

                if not is_due:
                    skipped_count += 1
                    continue

                already_sent = NotificationLog.objects.filter(
                    user=user,
                    date=user_today,
                    notification_key=item["key"],
                ).exists()

                if already_sent:
                    skipped_count += 1
                    continue

                payload = {
                    "head": item["title"],
                    "body": item["body"],
                    "url": item["url"],
                }

                if options["dry_run"]:
                    self.stdout.write(
                        self.style.WARNING(
                            f"[DRY RUN] {user.username} "
                            f"({user_tz.key}) "
                            f"{user_now.strftime('%H:%M')} — "
                            f"{item['key']} — {item['title']}"
                        )
                    )
                    continue

                try:
                    send_user_notification(
                        user=user,
                        payload=payload,
                        ttl=1000,
                    )

                    NotificationLog.objects.create(
                        user=user,
                        date=user_today,
                        notification_key=item["key"],
                        title=item["title"],
                    )

                    sent_count += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Sent to {user.username} "
                            f"({user_tz.key}) "
                            f"{item['key']} — {item['title']}"
                        )
                    )

                except Exception as error:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Failed for {user.username}: {item['key']} — {error}"
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Sent: {sent_count}. Skipped: {skipped_count}."
            )
        )