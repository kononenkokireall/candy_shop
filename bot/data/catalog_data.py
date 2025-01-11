# Default value for repeated price
DEFAULT_PRICE = 19


# Function to create an item structure for better reusability
def create_item(item_id, item_name, item_description, item_price=DEFAULT_PRICE):
    return {
        "id": item_id,
        "name": item_name,
        "description": item_description.strip(),
        "price": item_price,
    }


# Refactored product catalog
PRODUCT_CATALOG = {
    "lollipops": {
        "category_name": "Cannabis Lollipops",
        "items": [
            create_item(
                "101",
                "Hemperium's Original",
                """Оригинальные леденцы с каннабисом от Hemperium.
                Леденцы с каннабисом от Hemperium стали первыми победителями
                Кубка каннабиса HIGH TIMES. Еще в 1999 году Hemperium
                с гордостью выпустил свой первый продукт собственной
                разработки из каннабиса: оригинальные леденцы
                Cannabis Lollipops, изготовленные из 100% натурального масла каннабиса.
                Они имели огромный успех и выиграли High Times Cannabis Cup в Амстердаме
                в номинации «Лучший продукт», а затем еще один первый приз
                на Haarlem Hemp Awards несколько недель спустя.
                Теперь, спустя более двух десятилетий после их появления,
                они по-прежнему, если не больше, являются одними из самых популярных
                в мире лакомств из каннабиса.
                Присоединяйтесь к нам, чтобы отпраздновать это знаменательное событие
                выпуском эксклюзивного юбилейного издания!"""
            ),
            create_item(
                "102",
                "Bubblegum x Candy Kush",
                """В 1999 году Hemperium с гордостью выпустила первый
                 продукт из каннабиса: оригинальные леденцы,
                 изготовленные из 100% настоящего европейского масла каннабиса.
                 Компания получила награды High Times Cannabis Cup и Haarlem Hemp Awards"""
            ),
            create_item(
                "103",
                "Northern Lights x Pineapple Express",
                """Вместе с оцененным наградами Hemperium,
                Dr. Greenlove производит качественные леденцы из каннабиса
                с уникальными вкусами, такими как Northern Lights x Pineapple Express."""
            ),
        ]
    },
    "accessories": {
        "category_name": "Thimbles",
        "items": [
            create_item(
                "201",
                "Orange Thimbles",
                "Standard accessory description.",
                item_price=0  # Fixed typo from "prince" and set appropriate price
            )
        ]
    },
}
