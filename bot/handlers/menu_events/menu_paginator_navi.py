from utilit.paginator import Paginator


# Функция для создания кнопок постраничной навигации
def pages(paginator: Paginator) -> dict[str, str]:
    btn: dict[str, str] = {}
    # Если доступна предыдущая страница, добавляем кнопку "Пред."
    if paginator.has_previous():
        btn["◀️Пред."] = "prev"
    # Если доступна следующая страница, добавляем кнопку "След."
    if paginator.has_next():
        btn["След.▶️"] = "next"
    return btn
