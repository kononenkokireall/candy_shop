# Функция для создания кнопок постраничной навигации
from utilit.paginator import Paginator


def pages(paginator: Paginator) -> dict[str, str]:
    btn = {}
    # Если доступна предыдущая страница, добавляем кнопку "Пред."
    if paginator.has_previous():
        btn["◀️Пред."] = "prev"
    # Если доступна следующая страница, добавляем кнопку "След."
    if paginator.has_next():
        btn["След.▶️"] = "next"
    return btn
