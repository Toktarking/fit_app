from django.core.management.base import BaseCommand

from planner.models import (
    Food,
    Dish,
    DishIngredient,
    Exercise,
    WorkoutTemplate,
    WorkoutTemplateExercise,
)


class Command(BaseCommand):
    help = "Seed basic fitness foods, dishes, exercises, and workout templates."

    def handle(self, *args, **options):
        self.create_foods()
        self.create_dishes()
        self.create_exercises()
        self.create_workout_templates()

        self.stdout.write(
            self.style.SUCCESS("Fitness seed data created successfully.")
        )

    def create_foods(self):
        foods = [
            # Белок
            ("Куриная грудка", Food.Category.PROTEIN, 165, 31, 3.6, 0),
            ("Куриное бедро без кожи", Food.Category.PROTEIN, 185, 25, 9, 0),
            ("Индейка", Food.Category.PROTEIN, 135, 29, 1.5, 0),
            ("Говядина нежирная", Food.Category.PROTEIN, 190, 26, 9, 0),
            ("Рыба", Food.Category.PROTEIN, 140, 22, 5, 0),
            ("Тунец консервированный", Food.Category.PROTEIN, 120, 26, 1, 0),
            ("Яйцо", Food.Category.PROTEIN, 155, 13, 11, 1.1),
            ("Фасоль", Food.Category.PROTEIN, 120, 8, 0.5, 21),
            ("Чечевица", Food.Category.PROTEIN, 116, 9, 0.4, 20),
            ("Нут", Food.Category.PROTEIN, 164, 9, 2.6, 27),

            # Молочные продукты
            ("Творог 5%", Food.Category.DAIRY, 121, 17, 5, 3),
            ("Кефир 1%", Food.Category.DAIRY, 40, 3, 1, 4),
            ("Йогурт без сахара", Food.Category.DAIRY, 65, 5, 2, 6),
            ("Молоко 2.5%", Food.Category.DAIRY, 52, 3, 2.5, 5),
            ("Айран", Food.Category.DAIRY, 35, 2, 1, 4),
            ("Сыр", Food.Category.FAT, 350, 25, 27, 2),

            # Углеводы
            ("Овсянка", Food.Category.CARB, 370, 13, 7, 60),
            ("Рис", Food.Category.CARB, 340, 7, 1, 75),
            ("Гречка", Food.Category.CARB, 330, 13, 3, 68),
            ("Булгур", Food.Category.CARB, 342, 12, 1.3, 76),
            ("Перловка", Food.Category.CARB, 320, 9, 1, 73),
            ("Картофель", Food.Category.CARB, 77, 2, 0.1, 17),
            ("Макароны твердых сортов", Food.Category.CARB, 350, 12, 1.5, 72),
            ("Хлеб цельнозерновой", Food.Category.CARB, 230, 8, 3, 42),
            ("Лаваш", Food.Category.CARB, 280, 8, 1.5, 56),

            # Овощи
            ("Огурец", Food.Category.VEGETABLE, 15, 0.7, 0.1, 3),
            ("Помидор", Food.Category.VEGETABLE, 18, 0.9, 0.2, 3.9),
            ("Капуста", Food.Category.VEGETABLE, 25, 1.3, 0.1, 6),
            ("Морковь", Food.Category.VEGETABLE, 41, 0.9, 0.2, 10),
            ("Овощной салат", Food.Category.VEGETABLE, 25, 1.2, 0.2, 5),

            # Фрукты / сладкое
            ("Банан", Food.Category.FRUIT, 89, 1.1, 0.3, 23),
            ("Яблоко", Food.Category.FRUIT, 52, 0.3, 0.2, 14),
            ("Ягоды", Food.Category.FRUIT, 50, 1, 0.3, 12),
            ("Изюм", Food.Category.FRUIT, 299, 3, 0.5, 79),
            ("Мед", Food.Category.CARB, 304, 0, 0, 82),

            # Жиры
            ("Орехи", Food.Category.FAT, 600, 20, 50, 20),
            ("Оливковое масло", Food.Category.FAT, 884, 0, 100, 0),
            ("Арахисовая паста", Food.Category.FAT, 588, 25, 50, 20),

            # Напитки / другое
            ("Чай без сахара", Food.Category.DRINK, 1, 0, 0, 0),
            ("Кофе без сахара", Food.Category.DRINK, 2, 0, 0, 0),
        ]

        for name, category, calories, protein, fat, carbs in foods:
            Food.objects.update_or_create(
                name=name,
                defaults={
                    "category": category,
                    "calories_per_100g": calories,
                    "protein_per_100g": protein,
                    "fat_per_100g": fat,
                    "carbs_per_100g": carbs,
                    "is_common": True,
                },
            )

        self.stdout.write(self.style.SUCCESS("Foods created."))

    def create_dishes(self):
        dishes = [
            # =========================
            # ЗАВТРАКИ
            # =========================
            {
                "title": "Овсянка с яйцами и яблоком",
                "meal_type": Dish.MealType.BREAKFAST,
                "calories": 470,
                "protein_g": 27,
                "fat_g": 16,
                "carbs_g": 55,
                "cooking_time_minutes": 15,
                "description": "Хороший завтрак после утренней ходьбы или легкого бега.",
                "cooking_steps": (
                    "1. Отварите овсянку на воде 7–10 минут.\n"
                    "2. Яйца сварите или приготовьте на сковороде без лишнего масла.\n"
                    "3. Нарежьте яблоко.\n"
                    "4. Подайте все вместе."
                ),
                "ingredients": [
                    ("Овсянка", 60),
                    ("Яйцо", 100),
                    ("Яблоко", 150),
                ],
            },
            {
                "title": "Овсянка с бананом, орехами и яйцами",
                "meal_type": Dish.MealType.BREAKFAST,
                "calories": 620,
                "protein_g": 32,
                "fat_g": 24,
                "carbs_g": 72,
                "cooking_time_minutes": 15,
                "description": "Сытный завтрак для дней с высокой активностью.",
                "cooking_steps": (
                    "1. Отварите овсянку на воде или молоке.\n"
                    "2. Банан нарежьте кружочками.\n"
                    "3. Яйца сварите отдельно.\n"
                    "4. Добавьте орехи в овсянку и подайте вместе."
                ),
                "ingredients": [
                    ("Овсянка", 70),
                    ("Банан", 120),
                    ("Орехи", 20),
                    ("Яйцо", 100),
                ],
            },
            {
                "title": "Творог с бананом и орехами",
                "meal_type": Dish.MealType.BREAKFAST,
                "calories": 455,
                "protein_g": 34,
                "fat_g": 15,
                "carbs_g": 45,
                "cooking_time_minutes": 5,
                "description": "Быстрый белковый завтрак без готовки.",
                "cooking_steps": (
                    "1. Выложите творог в тарелку.\n"
                    "2. Нарежьте банан.\n"
                    "3. Добавьте орехи.\n"
                    "4. Перемешайте или ешьте отдельно."
                ),
                "ingredients": [
                    ("Творог 5%", 200),
                    ("Банан", 120),
                    ("Орехи", 15),
                ],
            },
            {
                "title": "Творог с бананом, хлебом и сыром",
                "meal_type": Dish.MealType.BREAKFAST,
                "calories": 620,
                "protein_g": 42,
                "fat_g": 22,
                "carbs_g": 62,
                "cooking_time_minutes": 7,
                "description": "Сытный завтрак, если нужно добрать калории и белок.",
                "cooking_steps": (
                    "1. Выложите творог в тарелку.\n"
                    "2. Нарежьте банан.\n"
                    "3. Сделайте бутерброд из цельнозернового хлеба и сыра.\n"
                    "4. Подайте вместе."
                ),
                "ingredients": [
                    ("Творог 5%", 200),
                    ("Банан", 120),
                    ("Хлеб цельнозерновой", 70),
                    ("Сыр", 30),
                ],
            },
            {
                "title": "Омлет с хлебом и овощами",
                "meal_type": Dish.MealType.BREAKFAST,
                "calories": 490,
                "protein_g": 31,
                "fat_g": 22,
                "carbs_g": 38,
                "cooking_time_minutes": 15,
                "description": "Сытный завтрак для дней с силовой тренировкой.",
                "cooking_steps": (
                    "1. Взбейте яйца вилкой.\n"
                    "2. Приготовьте омлет на сковороде с минимальным количеством масла.\n"
                    "3. Нарежьте огурец и помидор.\n"
                    "4. Подайте с хлебом."
                ),
                "ingredients": [
                    ("Яйцо", 150),
                    ("Хлеб цельнозерновой", 70),
                    ("Помидор", 100),
                    ("Огурец", 100),
                ],
            },
            {
                "title": "Омлет с сыром, хлебом и овощами",
                "meal_type": Dish.MealType.BREAKFAST,
                "calories": 640,
                "protein_g": 39,
                "fat_g": 34,
                "carbs_g": 42,
                "cooking_time_minutes": 15,
                "description": "Более калорийный вариант омлета для активного дня.",
                "cooking_steps": (
                    "1. Взбейте яйца.\n"
                    "2. Добавьте сыр в омлет ближе к концу приготовления.\n"
                    "3. Нарежьте овощи.\n"
                    "4. Подайте с цельнозерновым хлебом."
                ),
                "ingredients": [
                    ("Яйцо", 180),
                    ("Сыр", 35),
                    ("Хлеб цельнозерновой", 80),
                    ("Овощной салат", 150),
                ],
            },
            {
                "title": "Гречка с яйцами и овощами",
                "meal_type": Dish.MealType.BREAKFAST,
                "calories": 460,
                "protein_g": 26,
                "fat_g": 15,
                "carbs_g": 55,
                "cooking_time_minutes": 20,
                "description": "Простой завтрак из обычных продуктов.",
                "cooking_steps": (
                    "1. Отварите гречку.\n"
                    "2. Яйца сварите или приготовьте на сковороде.\n"
                    "3. Добавьте овощной салат.\n"
                    "4. Подайте теплым."
                ),
                "ingredients": [
                    ("Гречка", 60),
                    ("Яйцо", 100),
                    ("Овощной салат", 150),
                ],
            },
            {
                "title": "Рисовая каша с молоком, бананом и яйцами",
                "meal_type": Dish.MealType.BREAKFAST,
                "calories": 590,
                "protein_g": 28,
                "fat_g": 17,
                "carbs_g": 82,
                "cooking_time_minutes": 20,
                "description": "Альтернатива овсянке, хорошо подходит перед активным днем.",
                "cooking_steps": (
                    "1. Отварите рис до мягкости.\n"
                    "2. Добавьте молоко и прогрейте 2–3 минуты.\n"
                    "3. Нарежьте банан.\n"
                    "4. Яйца сварите отдельно и подайте вместе."
                ),
                "ingredients": [
                    ("Рис", 70),
                    ("Молоко 2.5%", 200),
                    ("Банан", 100),
                    ("Яйцо", 100),
                ],
            },

            # =========================
            # ОБЕДЫ
            # =========================
            {
                "title": "Курица с рисом и салатом",
                "meal_type": Dish.MealType.LUNCH,
                "calories": 650,
                "protein_g": 55,
                "fat_g": 15,
                "carbs_g": 75,
                "cooking_time_minutes": 30,
                "description": "Базовый обед для похудения и сохранения мышц.",
                "cooking_steps": (
                    "1. Отварите рис.\n"
                    "2. Куриную грудку отварите, запеките или приготовьте на сковороде.\n"
                    "3. Подготовьте овощной салат.\n"
                    "4. Добавьте оливковое масло в салат."
                ),
                "ingredients": [
                    ("Куриная грудка", 180),
                    ("Рис", 90),
                    ("Овощной салат", 200),
                    ("Оливковое масло", 10),
                ],
            },
            {
                "title": "Курица с рисом, салатом, маслом и хлебом",
                "meal_type": Dish.MealType.LUNCH,
                "calories": 820,
                "protein_g": 62,
                "fat_g": 22,
                "carbs_g": 100,
                "cooking_time_minutes": 30,
                "description": "Сытный обед для дневной цели 2200+ ккал.",
                "cooking_steps": (
                    "1. Отварите рис.\n"
                    "2. Приготовьте куриную грудку.\n"
                    "3. Сделайте овощной салат с маслом.\n"
                    "4. Добавьте цельнозерновой хлеб."
                ),
                "ingredients": [
                    ("Куриная грудка", 200),
                    ("Рис", 110),
                    ("Овощной салат", 250),
                    ("Оливковое масло", 15),
                    ("Хлеб цельнозерновой", 50),
                ],
            },
            {
                "title": "Говядина с гречкой и овощами",
                "meal_type": Dish.MealType.LUNCH,
                "calories": 680,
                "protein_g": 48,
                "fat_g": 22,
                "carbs_g": 70,
                "cooking_time_minutes": 35,
                "description": "Плотный обед в день силовой тренировки.",
                "cooking_steps": (
                    "1. Отварите гречку.\n"
                    "2. Говядину потушите или приготовьте на сковороде.\n"
                    "3. Добавьте овощной салат.\n"
                    "4. Подайте теплым."
                ),
                "ingredients": [
                    ("Говядина нежирная", 170),
                    ("Гречка", 90),
                    ("Овощной салат", 200),
                ],
            },
            {
                "title": "Говядина с картофелем и салатом",
                "meal_type": Dish.MealType.LUNCH,
                "calories": 780,
                "protein_g": 50,
                "fat_g": 25,
                "carbs_g": 88,
                "cooking_time_minutes": 40,
                "description": "Домашний сытный обед из обычных продуктов.",
                "cooking_steps": (
                    "1. Картофель отварите или запеките.\n"
                    "2. Говядину потушите до мягкости.\n"
                    "3. Подготовьте овощной салат.\n"
                    "4. Подайте все вместе."
                ),
                "ingredients": [
                    ("Говядина нежирная", 190),
                    ("Картофель", 350),
                    ("Овощной салат", 250),
                    ("Оливковое масло", 10),
                ],
            },
            {
                "title": "Рыба с картофелем и салатом",
                "meal_type": Dish.MealType.LUNCH,
                "calories": 620,
                "protein_g": 45,
                "fat_g": 16,
                "carbs_g": 70,
                "cooking_time_minutes": 30,
                "description": "Легкий обед с хорошим белком.",
                "cooking_steps": (
                    "1. Картофель отварите или запеките.\n"
                    "2. Рыбу запеките, отварите или приготовьте на сковороде.\n"
                    "3. Сделайте овощной салат.\n"
                    "4. Добавьте немного оливкового масла."
                ),
                "ingredients": [
                    ("Рыба", 200),
                    ("Картофель", 300),
                    ("Овощной салат", 200),
                    ("Оливковое масло", 10),
                ],
            },
            {
                "title": "Курица с макаронами и овощами",
                "meal_type": Dish.MealType.LUNCH,
                "calories": 670,
                "protein_g": 52,
                "fat_g": 14,
                "carbs_g": 80,
                "cooking_time_minutes": 30,
                "description": "Вариант для тех, кто любит макароны.",
                "cooking_steps": (
                    "1. Отварите макароны твердых сортов.\n"
                    "2. Курицу приготовьте отдельно.\n"
                    "3. Добавьте овощной салат.\n"
                    "4. Перемешайте или подайте отдельно."
                ),
                "ingredients": [
                    ("Куриная грудка", 180),
                    ("Макароны твердых сортов", 90),
                    ("Овощной салат", 200),
                ],
            },
            {
                "title": "Индейка с булгуром и салатом",
                "meal_type": Dish.MealType.LUNCH,
                "calories": 720,
                "protein_g": 58,
                "fat_g": 16,
                "carbs_g": 82,
                "cooking_time_minutes": 30,
                "description": "Альтернатива курице и рису.",
                "cooking_steps": (
                    "1. Отварите булгур.\n"
                    "2. Индейку потушите или запеките.\n"
                    "3. Подготовьте овощной салат.\n"
                    "4. Добавьте масло в салат."
                ),
                "ingredients": [
                    ("Индейка", 200),
                    ("Булгур", 90),
                    ("Овощной салат", 250),
                    ("Оливковое масло", 10),
                ],
            },
            {
                "title": "Облегченный плов с курицей",
                "meal_type": Dish.MealType.LUNCH,
                "calories": 790,
                "protein_g": 50,
                "fat_g": 22,
                "carbs_g": 95,
                "cooking_time_minutes": 45,
                "description": "Более привычный сытный обед, но с контролируемым количеством масла.",
                "cooking_steps": (
                    "1. Нарежьте курицу и морковь.\n"
                    "2. Слегка потушите курицу с морковью.\n"
                    "3. Добавьте рис и воду.\n"
                    "4. Готовьте до мягкости риса.\n"
                    "5. Масло используйте умеренно."
                ),
                "ingredients": [
                    ("Куриное бедро без кожи", 200),
                    ("Рис", 110),
                    ("Морковь", 120),
                    ("Оливковое масло", 12),
                ],
            },
            {
                "title": "Тунец с рисом и овощами",
                "meal_type": Dish.MealType.LUNCH,
                "calories": 640,
                "protein_g": 48,
                "fat_g": 9,
                "carbs_g": 85,
                "cooking_time_minutes": 20,
                "description": "Быстрый обед, если нет времени долго готовить.",
                "cooking_steps": (
                    "1. Отварите рис.\n"
                    "2. Откройте тунец и слейте лишнюю жидкость.\n"
                    "3. Подготовьте овощной салат.\n"
                    "4. Смешайте или подайте отдельно."
                ),
                "ingredients": [
                    ("Тунец консервированный", 160),
                    ("Рис", 90),
                    ("Овощной салат", 250),
                    ("Оливковое масло", 5),
                ],
            },
            {
                "title": "Чечевица с курицей и овощами",
                "meal_type": Dish.MealType.LUNCH,
                "calories": 700,
                "protein_g": 58,
                "fat_g": 13,
                "carbs_g": 82,
                "cooking_time_minutes": 35,
                "description": "Сытный белково-углеводный обед.",
                "cooking_steps": (
                    "1. Отварите чечевицу.\n"
                    "2. Курицу приготовьте отдельно.\n"
                    "3. Добавьте овощной салат.\n"
                    "4. Подайте все вместе."
                ),
                "ingredients": [
                    ("Чечевица", 120),
                    ("Куриная грудка", 180),
                    ("Овощной салат", 200),
                ],
            },

            # =========================
            # ПОЛДНИКИ / ЗАКУСКИ
            # =========================
            {
                "title": "Кефир с бананом",
                "meal_type": Dish.MealType.SNACK,
                "calories": 270,
                "protein_g": 10,
                "fat_g": 3,
                "carbs_g": 50,
                "cooking_time_minutes": 3,
                "description": "Легкий перекус перед тренировкой.",
                "cooking_steps": (
                    "1. Налейте кефир.\n"
                    "2. Съешьте банан отдельно или нарежьте его к кефиру."
                ),
                "ingredients": [
                    ("Кефир 1%", 300),
                    ("Банан", 150),
                ],
            },
            {
                "title": "Йогурт с яблоком",
                "meal_type": Dish.MealType.SNACK,
                "calories": 250,
                "protein_g": 13,
                "fat_g": 5,
                "carbs_g": 38,
                "cooking_time_minutes": 3,
                "description": "Простой полдник для рабочего дня.",
                "cooking_steps": (
                    "1. Выложите йогурт в миску.\n"
                    "2. Нарежьте яблоко.\n"
                    "3. Перемешайте или ешьте отдельно."
                ),
                "ingredients": [
                    ("Йогурт без сахара", 250),
                    ("Яблоко", 180),
                ],
            },
            {
                "title": "Творог с ягодами",
                "meal_type": Dish.MealType.SNACK,
                "calories": 285,
                "protein_g": 28,
                "fat_g": 8,
                "carbs_g": 25,
                "cooking_time_minutes": 5,
                "description": "Белковый полдник, хорошо подходит для похудения.",
                "cooking_steps": (
                    "1. Выложите творог в тарелку.\n"
                    "2. Добавьте ягоды.\n"
                    "3. Перемешайте."
                ),
                "ingredients": [
                    ("Творог 5%", 180),
                    ("Ягоды", 100),
                ],
            },
            {
                "title": "Творог с бананом",
                "meal_type": Dish.MealType.SNACK,
                "calories": 390,
                "protein_g": 32,
                "fat_g": 9,
                "carbs_g": 48,
                "cooking_time_minutes": 5,
                "description": "Сытный белковый перекус.",
                "cooking_steps": (
                    "1. Выложите творог.\n"
                    "2. Нарежьте банан.\n"
                    "3. Перемешайте или ешьте отдельно."
                ),
                "ingredients": [
                    ("Творог 5%", 220),
                    ("Банан", 140),
                ],
            },
            {
                "title": "Яблоко с орехами и йогуртом",
                "meal_type": Dish.MealType.SNACK,
                "calories": 310,
                "protein_g": 12,
                "fat_g": 13,
                "carbs_g": 38,
                "cooking_time_minutes": 5,
                "description": "Сытный перекус, если хочется сладкого.",
                "cooking_steps": (
                    "1. Нарежьте яблоко.\n"
                    "2. Добавьте йогурт.\n"
                    "3. Орехи можно добавить сверху или съесть отдельно."
                ),
                "ingredients": [
                    ("Яблоко", 180),
                    ("Орехи", 15),
                    ("Йогурт без сахара", 150),
                ],
            },
            {
                "title": "Кефир с хлебом и сыром",
                "meal_type": Dish.MealType.SNACK,
                "calories": 410,
                "protein_g": 20,
                "fat_g": 17,
                "carbs_g": 42,
                "cooking_time_minutes": 5,
                "description": "Сытный перекус, если нужно добрать калории.",
                "cooking_steps": (
                    "1. Налейте кефир.\n"
                    "2. Сделайте бутерброд из хлеба и сыра.\n"
                    "3. Подайте вместе."
                ),
                "ingredients": [
                    ("Кефир 1%", 300),
                    ("Хлеб цельнозерновой", 60),
                    ("Сыр", 30),
                ],
            },
            {
                "title": "Банан с арахисовой пастой и йогуртом",
                "meal_type": Dish.MealType.SNACK,
                "calories": 430,
                "protein_g": 17,
                "fat_g": 19,
                "carbs_g": 52,
                "cooking_time_minutes": 5,
                "description": "Калорийный перекус перед тренировкой или после активного дня.",
                "cooking_steps": (
                    "1. Нарежьте банан.\n"
                    "2. Добавьте йогурт.\n"
                    "3. Добавьте арахисовую пасту сверху."
                ),
                "ingredients": [
                    ("Банан", 150),
                    ("Арахисовая паста", 25),
                    ("Йогурт без сахара", 200),
                ],
            },
            {
                "title": "Яйца с овощами",
                "meal_type": Dish.MealType.SNACK,
                "calories": 260,
                "protein_g": 19,
                "fat_g": 16,
                "carbs_g": 10,
                "cooking_time_minutes": 10,
                "description": "Белковый перекус без сладкого.",
                "cooking_steps": (
                    "1. Сварите яйца.\n"
                    "2. Нарежьте овощи.\n"
                    "3. Подайте вместе."
                ),
                "ingredients": [
                    ("Яйцо", 120),
                    ("Овощной салат", 150),
                ],
            },

            # =========================
            # УЖИНЫ
            # =========================
            {
                "title": "Курица с овощами",
                "meal_type": Dish.MealType.DINNER,
                "calories": 460,
                "protein_g": 48,
                "fat_g": 14,
                "carbs_g": 25,
                "cooking_time_minutes": 25,
                "description": "Легкий белковый ужин.",
                "cooking_steps": (
                    "1. Приготовьте куриную грудку.\n"
                    "2. Подготовьте овощной салат.\n"
                    "3. Добавьте немного оливкового масла.\n"
                    "4. Подайте вместе."
                ),
                "ingredients": [
                    ("Куриная грудка", 180),
                    ("Овощной салат", 250),
                    ("Оливковое масло", 10),
                ],
            },
            {
                "title": "Курица с гречкой и овощами",
                "meal_type": Dish.MealType.DINNER,
                "calories": 610,
                "protein_g": 55,
                "fat_g": 16,
                "carbs_g": 62,
                "cooking_time_minutes": 30,
                "description": "Нормальный сытный ужин после силовой тренировки.",
                "cooking_steps": (
                    "1. Отварите гречку.\n"
                    "2. Приготовьте куриную грудку.\n"
                    "3. Добавьте овощной салат.\n"
                    "4. Подайте теплым."
                ),
                "ingredients": [
                    ("Куриная грудка", 190),
                    ("Гречка", 70),
                    ("Овощной салат", 220),
                    ("Оливковое масло", 8),
                ],
            },
            {
                "title": "Рыба с гречкой и салатом",
                "meal_type": Dish.MealType.DINNER,
                "calories": 500,
                "protein_g": 42,
                "fat_g": 15,
                "carbs_g": 45,
                "cooking_time_minutes": 30,
                "description": "Хороший ужин после бассейна или силовой.",
                "cooking_steps": (
                    "1. Отварите гречку.\n"
                    "2. Рыбу запеките или приготовьте на сковороде.\n"
                    "3. Подготовьте овощной салат.\n"
                    "4. Подайте вместе."
                ),
                "ingredients": [
                    ("Рыба", 180),
                    ("Гречка", 50),
                    ("Овощной салат", 200),
                ],
            },
            {
                "title": "Рыба с картофелем и овощами",
                "meal_type": Dish.MealType.DINNER,
                "calories": 620,
                "protein_g": 46,
                "fat_g": 18,
                "carbs_g": 68,
                "cooking_time_minutes": 30,
                "description": "Сытный ужин после бассейна.",
                "cooking_steps": (
                    "1. Картофель отварите или запеките.\n"
                    "2. Рыбу приготовьте отдельно.\n"
                    "3. Добавьте овощной салат.\n"
                    "4. Подайте вместе."
                ),
                "ingredients": [
                    ("Рыба", 200),
                    ("Картофель", 280),
                    ("Овощной салат", 220),
                    ("Оливковое масло", 8),
                ],
            },
            {
                "title": "Омлет с овощами и творогом",
                "meal_type": Dish.MealType.DINNER,
                "calories": 480,
                "protein_g": 40,
                "fat_g": 24,
                "carbs_g": 22,
                "cooking_time_minutes": 15,
                "description": "Ужин без круп, но с высоким белком.",
                "cooking_steps": (
                    "1. Приготовьте омлет из яиц.\n"
                    "2. Добавьте овощной салат.\n"
                    "3. Творог подайте отдельно.\n"
                    "4. Хороший вариант, если не хочется круп."
                ),
                "ingredients": [
                    ("Яйцо", 150),
                    ("Творог 5%", 120),
                    ("Овощной салат", 200),
                ],
            },
            {
                "title": "Омлет с хлебом, сыром и овощами",
                "meal_type": Dish.MealType.DINNER,
                "calories": 650,
                "protein_g": 42,
                "fat_g": 35,
                "carbs_g": 45,
                "cooking_time_minutes": 15,
                "description": "Более сытный ужин на день с высокой активностью.",
                "cooking_steps": (
                    "1. Приготовьте омлет.\n"
                    "2. Добавьте сыр в конце приготовления.\n"
                    "3. Подайте с хлебом и овощами.\n"
                    "4. Масло используйте умеренно."
                ),
                "ingredients": [
                    ("Яйцо", 180),
                    ("Сыр", 35),
                    ("Хлеб цельнозерновой", 80),
                    ("Овощной салат", 200),
                ],
            },
            {
                "title": "Говядина с овощами",
                "meal_type": Dish.MealType.DINNER,
                "calories": 520,
                "protein_g": 42,
                "fat_g": 24,
                "carbs_g": 25,
                "cooking_time_minutes": 35,
                "description": "Плотный ужин для дня с высокой активностью.",
                "cooking_steps": (
                    "1. Говядину потушите или приготовьте на сковороде.\n"
                    "2. Подготовьте овощной салат.\n"
                    "3. Добавьте немного масла.\n"
                    "4. Подайте вместе."
                ),
                "ingredients": [
                    ("Говядина нежирная", 180),
                    ("Овощной салат", 250),
                    ("Оливковое масло", 10),
                ],
            },
            {
                "title": "Говядина с картофелем и салатом",
                "meal_type": Dish.MealType.DINNER,
                "calories": 720,
                "protein_g": 48,
                "fat_g": 26,
                "carbs_g": 75,
                "cooking_time_minutes": 40,
                "description": "Сытный ужин после тяжелого дня или тренировки.",
                "cooking_steps": (
                    "1. Картофель отварите или запеките.\n"
                    "2. Говядину потушите до мягкости.\n"
                    "3. Сделайте овощной салат.\n"
                    "4. Подайте вместе."
                ),
                "ingredients": [
                    ("Говядина нежирная", 190),
                    ("Картофель", 300),
                    ("Овощной салат", 220),
                    ("Оливковое масло", 8),
                ],
            },
            {
                "title": "Индейка с рисом и салатом",
                "meal_type": Dish.MealType.DINNER,
                "calories": 620,
                "protein_g": 58,
                "fat_g": 10,
                "carbs_g": 72,
                "cooking_time_minutes": 30,
                "description": "Легкий, но сытный ужин с высоким белком.",
                "cooking_steps": (
                    "1. Отварите рис.\n"
                    "2. Индейку приготовьте на сковороде или запеките.\n"
                    "3. Добавьте овощной салат.\n"
                    "4. Подайте вместе."
                ),
                "ingredients": [
                    ("Индейка", 200),
                    ("Рис", 75),
                    ("Овощной салат", 220),
                    ("Оливковое масло", 5),
                ],
            },
        ]

        for dish_data in dishes:
            ingredients = dish_data.pop("ingredients")

            dish, _ = Dish.objects.update_or_create(
                title=dish_data["title"],
                defaults=dish_data,
            )

            dish.ingredients.all().delete()

            for food_name, grams in ingredients:
                food = Food.objects.get(name=food_name)

                DishIngredient.objects.create(
                    dish=dish,
                    food=food,
                    grams=grams,
                )

        self.stdout.write(self.style.SUCCESS("Dishes created."))

    def create_exercises(self):
        exercises = [
            ("Разминка на дорожке", "Кардио", Exercise.Difficulty.EASY, "Беговая дорожка"),
            ("Жим ногами", "Ноги", Exercise.Difficulty.EASY, "Тренажер"),
            ("Присед с собственным весом", "Ноги", Exercise.Difficulty.EASY, "Без оборудования"),
            ("Гоблет-присед", "Ноги", Exercise.Difficulty.EASY, "Гантель"),
            ("Выпады", "Ноги", Exercise.Difficulty.EASY, "Гантели/без оборудования"),
            ("Ягодичный мост", "Ягодицы", Exercise.Difficulty.EASY, "Без оборудования"),
            ("Жим в тренажере", "Грудь", Exercise.Difficulty.EASY, "Тренажер"),
            ("Отжимания от опоры", "Грудь", Exercise.Difficulty.EASY, "Без оборудования"),
            ("Тяга верхнего блока", "Спина", Exercise.Difficulty.EASY, "Тренажер"),
            ("Горизонтальная тяга", "Спина", Exercise.Difficulty.EASY, "Тренажер"),
            ("Тяга гантели в наклоне", "Спина", Exercise.Difficulty.MEDIUM, "Гантель"),
            ("Румынская тяга", "Задняя поверхность бедра", Exercise.Difficulty.MEDIUM, "Штанга/гантели"),
            ("Сгибание ног в тренажере", "Задняя поверхность бедра", Exercise.Difficulty.EASY, "Тренажер"),
            ("Жим гантелей сидя", "Плечи", Exercise.Difficulty.EASY, "Гантели"),
            ("Подъемы на носки", "Икры", Exercise.Difficulty.EASY, "Тренажер/гантели"),
            ("Планка", "Пресс", Exercise.Difficulty.EASY, "Без оборудования"),
            ("Скручивания", "Пресс", Exercise.Difficulty.EASY, "Без оборудования"),
            ("Боковая планка", "Пресс", Exercise.Difficulty.EASY, "Без оборудования"),
            ("Велотренажер", "Кардио", Exercise.Difficulty.EASY, "Велотренажер"),
            ("Эллипс", "Кардио", Exercise.Difficulty.EASY, "Эллиптический тренажер"),
            ("Легкое плавание", "Кардио", Exercise.Difficulty.EASY, "Бассейн"),
            ("Плавание интервалами", "Кардио", Exercise.Difficulty.MEDIUM, "Бассейн"),
            ("Растяжка ног", "Восстановление", Exercise.Difficulty.EASY, "Коврик"),
            ("Растяжка спины", "Восстановление", Exercise.Difficulty.EASY, "Коврик"),
        ]

        for name, muscle_group, difficulty, equipment in exercises:
            Exercise.objects.update_or_create(
                name=name,
                defaults={
                    "muscle_group": muscle_group,
                    "difficulty": difficulty,
                    "equipment": equipment,
                    "description": "",
                },
            )

        self.stdout.write(self.style.SUCCESS("Exercises created."))

    def create_workout_templates(self):
        templates = [
            {
                "title": "Силовая A",
                "workout_type": WorkoutTemplate.WorkoutType.STRENGTH,
                "duration_minutes": 50,
                "description": "Full Body A для новичка: техника, базовая сила, умеренная нагрузка.",
                "exercises": [
                    # exercise_name, sets, reps, rest_seconds, estimated_minutes, order
                    ("Разминка на дорожке", 1, "7–10 минут", 60, 8, 1),
                    ("Жим ногами", 3, "10–12", 90, 8, 2),
                    ("Жим в тренажере", 3, "10", 90, 7, 3),
                    ("Тяга верхнего блока", 3, "10", 90, 7, 4),
                    ("Румынская тяга", 3, "10", 90, 8, 5),
                    ("Планка", 3, "20–30 секунд", 60, 5, 6),
                ],
            },
            {
                "title": "Силовая B",
                "workout_type": WorkoutTemplate.WorkoutType.STRENGTH,
                "duration_minutes": 50,
                "description": "Full Body B для новичка: ноги, спина, плечи, пресс.",
                "exercises": [
                    ("Разминка на дорожке", 1, "7–10 минут", 60, 8, 1),
                    ("Гоблет-присед", 3, "10", 90, 8, 2),
                    ("Горизонтальная тяга", 3, "10", 90, 7, 3),
                    ("Жим гантелей сидя", 3, "10", 90, 7, 4),
                    ("Сгибание ног в тренажере", 3, "12", 90, 7, 5),
                    ("Скручивания", 3, "12–15", 60, 5, 6),
                ],
            },
            {
                "title": "Силовая C",
                "workout_type": WorkoutTemplate.WorkoutType.STRENGTH,
                "duration_minutes": 55,
                "description": "Дополнительная Full Body тренировка для последующих этапов.",
                "exercises": [
                    ("Разминка на дорожке", 1, "7–10 минут", 60, 8, 1),
                    ("Выпады", 3, "10 на каждую ногу", 90, 8, 2),
                    ("Тяга гантели в наклоне", 3, "10", 90, 8, 3),
                    ("Отжимания от опоры", 3, "8–12", 90, 7, 4),
                    ("Ягодичный мост", 3, "12–15", 60, 6, 5),
                    ("Боковая планка", 2, "20–30 секунд", 60, 5, 6),
                ],
            },
            {
                "title": "Бассейн восстановительный",
                "workout_type": WorkoutTemplate.WorkoutType.SWIMMING,
                "duration_minutes": 35,
                "description": "Спокойное плавание для восстановления после бега и зала.",
                "exercises": [
                    ("Легкое плавание", 1, "5 минут разминка", 60, 5, 1),
                    ("Легкое плавание", 8, "1 дорожка спокойно", 60, 20, 2),
                    ("Легкое плавание", 1, "5 минут заминка", 60, 5, 3),
                ],
            },
            {
                "title": "Бассейн интервальный",
                "workout_type": WorkoutTemplate.WorkoutType.SWIMMING,
                "duration_minutes": 40,
                "description": "Плавание в среднем темпе для выносливости и расхода калорий.",
                "exercises": [
                    ("Легкое плавание", 1, "5 минут разминка", 60, 5, 1),
                    ("Плавание интервалами", 6, "2 дорожки спокойно + 1 быстрее", 90, 30, 2),
                    ("Легкое плавание", 1, "5 минут заминка", 60, 5, 3),
                ],
            },
            {
                "title": "Растяжка и восстановление",
                "workout_type": WorkoutTemplate.WorkoutType.STRETCHING,
                "duration_minutes": 20,
                "description": "Легкая растяжка после активной недели.",
                "exercises": [
                    ("Растяжка ног", 3, "30–40 секунд", 30, 7, 1),
                    ("Растяжка спины", 3, "30–40 секунд", 30, 7, 2),
                    ("Боковая планка", 2, "20 секунд", 45, 5, 3),
                ],
            },
        ]

        for template_data in templates:
            exercises = template_data.pop("exercises")

            template, _ = WorkoutTemplate.objects.update_or_create(
                title=template_data["title"],
                defaults=template_data,
            )

            template.exercises.all().delete()

            for (
                exercise_name,
                sets,
                reps,
                rest_seconds,
                estimated_minutes,
                order,
            ) in exercises:
                exercise = Exercise.objects.get(name=exercise_name)

                WorkoutTemplateExercise.objects.create(
                    workout_template=template,
                    exercise=exercise,
                    sets=sets,
                    reps=reps,
                    rest_seconds=rest_seconds,
                    estimated_minutes=estimated_minutes,
                    order=order,
                )

        self.stdout.write(self.style.SUCCESS("Workout templates created."))