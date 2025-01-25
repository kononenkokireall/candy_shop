from aiogram.utils.formatting import Bold, as_list, as_marked_section


categories_goods = ['Cannabis Lollipops', 'Колпаки']

description_for_info_pages = {
    "main": "Добро пожаловать!",
    "about": "Магазин CBDS_Candies.\nРежим роботы - 14:00 - 18:00",
    "payment": as_marked_section(
        Bold("Способы оплаты:"),
        "BLIK: +49........",
        "TON Wallet",
        marker="💰"
    ).as_html(),
    "shipping": as_list(
        as_marked_section(
            Bold("Способы доставки/заказа:"),
            "Почтомат",
            "Самовывоз",
            marker="📦",
        ),
        as_marked_section(
            Bold("Не отправляем ...."),
            "Голубями",
            marker="❌"
        ),
        sep="\n-------------------------\n",
    ).as_html(),
    "catalog": "Категории",
    "cart": "В корзине нет товаров!"
}