"""
Locust load-test for Telegram-bot webhook.

⚙️  Запуск (пример внутри той же docker-сети):
    locust -f locust file.py \
           --headless -u 300 -r 10 -t 10m \
           --host http://telegram-bot:8080
"""
from pathlib import Path

from locust import HttpUser, task, between, LoadTestShape
import random
import time
import json
import logging
import os

# ──────────────────────── данные для «каталога» ──────────────────────────────
DATA_FILE = Path(__file__).with_name("test_products.json")
with open(DATA_FILE, "r", encoding="utf-8") as f:
    PRODUCTS = json.load(f)

# Путь веб хука относительно host (начинается с "/")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")

# ──────────────────────── форма нагрузки (ступени) ───────────────────────────
class RealisticLoadShape(LoadTestShape):
    """
    0-2 мин→50 юзеров, разгон 2/сек
    2-5 мин  → 200 юзеров, разгон 5/сек
    5-7 мин  → 100 юзеров, разгон 2/сек
    7-10 мин → 300 юзеров, разгон 10/сек (stress)
    """
    stages = [
        {"duration": 120, "users": 50,  "spawn_rate": 2},
        {"duration": 300, "users": 200, "spawn_rate": 5},
        {"duration": 420, "users": 100, "spawn_rate": 2},
        {"duration": 600, "users": 300, "spawn_rate": 10},
    ]

    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None


# ───────────────────────── основной «пользователь» ──────────────────────────
class BotUser(HttpUser):
    wait_time = between(0.5, 2.5)            # реалистичные паузы
    host = os.getenv("LOCUST_HOST") or ""    # задаётся из CLI (--host)

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.selected_products = None
        self.user_id = None

    def on_start(self):
        self.user_id = random.randint(100_000, 999_999)
        self.selected_products: list[dict] = []

        self._send_command("/start", name="/start (login)")

    # ────────────────────────── задачи Locust ────────────────────────────────
    @task(15)
    def view_main_menu(self):
        self._send_callback("main_menu", name="main_menu")

    @task(25)
    def browse_products(self):
        cat = random.choice(PRODUCTS["categories"])
        page = random.randint(1, 5)
        self._send_callback(f"browse:{cat['id']}:{page}", name="/browse_products")

    @task(20)
    def product_interaction(self):
        product = random.choice(PRODUCTS["items"])
        self._send_callback(f"view_product:{product['id']}", name="/view_product")

    @task(10)
    def add_to_cart(self):
        if not self.selected_products:
            self.selected_products = random.sample(PRODUCTS["items"], k=3)

        product = random.choice(self.selected_products)
        self._send_callback(f"add_to_cart:{product['id']}", name="/add_to_cart")

    @task(5)
    def checkout_process(self):
        self.add_to_cart()
        self._send_callback("preview_order", name="/preview_order")
        self._send_callback("confirm_payment", name="/confirm_payment")

    @task(2)
    def error_scenarios(self):
        # несуществующая команда
        self._send_command("/invalid_command", name="/invalid_command")
        # несуществующий товар
        self._send_callback("view_product:999999", name="/invalid_product")

    def on_stop(self):
        logging.info("User %s finished", self.user_id)

    # ────────────────────── вспомогательные методы ──────────────────────────
    def _send_command(self, text: str, *, name: str):
        """Отправка текстовой команды как update"""
        payload = {
            "update_id": random.randint(1, 1_000_000),
            "message": {
                "message_id": random.randint(1, 1_000_000),
                "from": {"id": self.user_id, "first_name": f"U{self.user_id}"},
                "chat": {"id": self.user_id},
                "text": text,
                "date": int(time.time()),
            },
        }
        self._post_json(payload, name)

    def _send_callback(self, data: str, *, name: str):
        """Отправка callback_query"""
        payload = {
            "callback_query": {
                "id": str(random.randint(1, 1_000_000)),
                "from": {"id": self.user_id, "first_name": f"U{self.user_id}"},
                "message": {"chat": {"id": self.user_id}},
                "data": data,
            }
        }
        self._post_json(payload, name)

    def _post_json(self, payload: dict, name: str):
        with self.client.post(
            WEBHOOK_PATH, json=payload, name=name, catch_response=True
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"{name} → {resp.status_code}: {resp.text}")
            else:
                resp.success()
