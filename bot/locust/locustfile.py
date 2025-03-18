from locust import HttpUser, task, between, LoadTestShape
import random
import time
import json
import logging

# Загрузка тестовых данных
with open("test_products.json") as f:
    PRODUCTS = json.load(f)


class RealisticLoadShape(LoadTestShape):
    stages = [
        {"duration": 120, "users": 50, "spawn_rate": 2},  # Постепенный рост
        {"duration": 300, "users": 200, "spawn_rate": 5},  # Пиковая нагрузка
        {"duration": 420, "users": 100, "spawn_rate": 2},  # Снижение нагрузки
        {"duration": 600, "users": 300, "spawn_rate": 10},  # Стресс-тест
    ]

    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        return None


class BotUser(HttpUser):
    wait_time = between(0.5, 5)  # Более реалистичные задержки
    host = "https://api.telegram.org/bot7633796438:AAFkTeA7cLYb3Js2EvlqJLo0UAgmiuSg94U"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = random.randint(100000, 999999)
        self.session_id = f"{self.user_id}-{int(time.time())}"
        self.selected_products = []

    def on_start(self):
        """Имитация начала сессии пользователя"""
        self.login()
        self.view_main_menu()

    def login(self):
        payload = {
            "update_id": random.randint(1, 1000),
            "message": {
                "message_id": random.randint(1, 1000),
                "from": {
                    "id": self.user_id,
                    "first_name": f"User{self.user_id}",
                    "last_name": f"Test{random.randint(1, 100)}",
                },
                "chat": {"id": self.user_id},
                "text": "/start",
                "date": int(time.time()),
            },
        }
        with self.client.post(
            "/webhook", json=payload, catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Login failed: {response.text}")

    @task(15)
    def view_main_menu(self):
        """Просмотр главного меню"""
        self.client.get("/")

    @task(25)
    def browse_products(self):
        """Просмотр товаров с фильтрацией"""
        category = random.choice(PRODUCTS["categories"])
        page = random.randint(1, 5)
        payload = {
            "callback_query": {
                "data": f"browse:{category['id']}:{page}",
                "message": {"chat": {"id": self.user_id}},
            }
        }
        self.client.post("/webhook", json=payload, name="/browse_products")

    @task(20)
    def product_interaction(self):
        """Просмотр деталей товара"""
        product = random.choice(PRODUCTS["items"])
        payload = {
            "callback_query": {
                "data": f"view_product:{product['id']}",
                "message": {"chat": {"id": self.user_id}},
            }
        }
        self.client.post("/webhook", json=payload, name="/view_product")

    @task(10)
    def add_to_cart(self):
        """Добавление в корзину"""
        if not self.selected_products:
            self.selected_products = random.sample(PRODUCTS["items"], k=3)

        product = random.choice(self.selected_products)
        payload = {
            "callback_query": {
                "data": f"add_to_cart:{product['id']}",
                "message": {"chat": {"id": self.user_id}},
            }
        }
        with self.client.post(
            "/webhook", json=payload, name="/add_to_cart"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to add product {product['id']}")

    @task(5)
    def checkout_process(self):
        """Полный процесс оформления заказа"""
        self.add_to_cart()
        self.preview_order()
        self.confirm_payment()

    def preview_order(self):
        payload = {
            "callback_query": {
                "data": "preview_order",
                "message": {"chat": {"id": self.user_id}},
            }
        }
        self.client.post("/webhook", json=payload, name="/preview_order")

    def confirm_payment(self):
        payload = {
            "callback_query": {
                "data": "confirm_payment",
                "message": {"chat": {"id": self.user_id}},
            }
        }
        self.client.post("/webhook", json=payload, name="/confirm_payment")

    @task(2)
    def error_scenarios(self):
        """Имитация ошибочных сценариев"""
        self.invalid_command()
        self.non_existent_product()

    def invalid_command(self):
        payload = {
            "message": {
                "chat": {"id": self.user_id},
                "text": "/invalid_command",
                "date": int(time.time()),
            }
        }
        self.client.post("/webhook", json=payload, name="/invalid_command")

    def non_existent_product(self):
        payload = {
            "callback_query": {
                "data": "view_product:999999",
                "message": {"chat": {"id": self.user_id}},
            }
        }
        self.client.post("/webhook", json=payload, name="/invalid_product")

    def on_stop(self):
        """Завершение сессии"""
        logging.info(f"User {self.user_id} session ended")
