from django import forms

from .models import FitnessProfile, ProgressCheckIn, ExtraFoodLog


TIMEZONE_CHOICES = [
    ("Asia/Almaty", "Казахстан — Алматы / Астана"),
    ("Asia/Aqtau", "Казахстан — Актау"),
    ("Asia/Aqtobe", "Казахстан — Актобе"),
    ("Asia/Oral", "Казахстан — Уральск"),
    ("Asia/Qyzylorda", "Казахстан — Кызылорда"),
    ("Asia/Tashkent", "Узбекистан"),
    ("Asia/Bishkek", "Кыргызстан"),
    ("Europe/Moscow", "Москва"),
    ("Europe/Istanbul", "Стамбул"),
    ("Europe/London", "Лондон"),
    ("Europe/Berlin", "Берлин"),
    ("America/New_York", "Нью-Йорк"),
    ("America/Los_Angeles", "Лос-Анджелес"),
]

class FitnessProfileForm(forms.ModelForm):
    timezone = forms.ChoiceField(
        choices=TIMEZONE_CHOICES,
        label="Ваш часовой пояс",
    )

    class Meta:
        model = FitnessProfile

        fields = [
            "gender",
            "age",
            "height_cm",
            "weight_kg",
            "goal",
            "activity_level",
            "has_gym",
            "wants_morning_running",
            "has_pool",
            "meals_per_day",
            "timezone",
        ]

        labels = {
            "gender": "Пол",
            "age": "Возраст",
            "height_cm": "Рост, см",
            "weight_kg": "Вес, кг",
            "goal": "Цель",
            "activity_level": "Уровень активности",
            "has_gym": "Есть доступ к залу",
            "wants_morning_running": "Хочу утренний бег/ходьбу",
            "has_pool": "Есть доступ к бассейну",
            "meals_per_day": "Сколько раз в день кушать",
        }


        help_texts = {
            "meals_per_day": "Для MVP лучше выбрать 4 приема пищи.",
        }

    def clean_meals_per_day(self):
        meals_per_day = self.cleaned_data["meals_per_day"]

        if meals_per_day not in [3, 4]:
            raise forms.ValidationError(
                "Пока приложение поддерживает 3 или 4 приема пищи. 5 добавим позже."
            )

        return meals_per_day


class ProgressCheckInForm(forms.ModelForm):
    class Meta:
        model = ProgressCheckIn
        fields = [
            "weight_kg",
            "waist_cm",
            "energy_level",
            "hunger_level",
            "comment",
        ]

        labels = {
            "weight_kg": "Вес, кг",
            "waist_cm": "Талия, см",
            "energy_level": "Энергия от 1 до 10",
            "hunger_level": "Голод от 1 до 10",
            "comment": "Комментарий",
        }

        widgets = {
            "weight_kg": forms.NumberInput(attrs={"step": "0.1"}),
            "waist_cm": forms.NumberInput(attrs={"step": "0.1"}),
            "energy_level": forms.NumberInput(attrs={"min": 1, "max": 10}),
            "hunger_level": forms.NumberInput(attrs={"min": 1, "max": 10}),
            "comment": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_energy_level(self):
        value = self.cleaned_data["energy_level"]

        if value < 1 or value > 10:
            raise forms.ValidationError("Энергия должна быть от 1 до 10.")

        return value

    def clean_hunger_level(self):
        value = self.cleaned_data["hunger_level"]

        if value < 1 or value > 10:
            raise forms.ValidationError("Голод должен быть от 1 до 10.")

        return value


class ExtraFoodLogForm(forms.ModelForm):
    class Meta:
        model = ExtraFoodLog
        fields = [
            "title",
            "quantity_description",
            "calories",
            "note",
        ]

        labels = {
            "title": "Что вы дополнительно съели?",
            "quantity_description": "Количество",
            "calories": "Примерно калорий",
            "note": "Комментарий",
        }

        help_texts = {
            "calories": "Можно указать примерно. Например: шоколадка 250 ккал, печенье 150 ккал, бургер 600 ккал.",
        }

        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "Например: шоколадка"}
            ),
            "quantity_description": forms.TextInput(
                attrs={"placeholder": "Например: 1 шт / 50 г / 1 стакан"}
            ),
            "calories": forms.NumberInput(
                attrs={"min": 1, "placeholder": "Например: 250"}
            ),
            "note": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Например: съел после обеда"}
            ),
        }

    def clean_calories(self):
        calories = self.cleaned_data["calories"]

        if calories <= 0:
            raise forms.ValidationError("Калории должны быть больше 0.")

        if calories > 3000:
            raise forms.ValidationError(
                "Слишком большое значение. Проверьте, правильно ли указали калории."
            )

        return calories