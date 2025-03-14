#!/usr/bin/env python3
import requests
from utilit.config import settings

def get_webhook_info():
    """
    Функция для получения информации о вебхуке Telegram-бота.
    Отправляет GET-запрос к методу getWebhookInfo.
    """
    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/getWebhookInfo"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверка на наличие HTTP ошибок
        return response.json()
    except requests.RequestException as e:
        print("Ошибка при запросе:", e)
        return None


if __name__ == "__main__":
    # Замените строку ниже на токен вашего Telegram-бота, полученный через BotFather.
    bot_token = settings.BOT_TOKEN

    webhook_info = get_webhook_info()
    if webhook_info:
        print("Информация о вебхуке:")
        print(webhook_info)
    else:
        print("Не удалось получить информацию о вебхуке.")
