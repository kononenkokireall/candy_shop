def dict_to_object(model_class, data):
    """
    Конвертирует словарь в объект SQLAlchemy.
    :param model_class: Класс модели SQLAlchemy (например, Product)
    :param data: Словарь, который нужно конвертировать в объект
    :return: Объект модели SQLAlchemy
    """
    return model_class(**data)

def get_attr(obj, attr, model_class=None):
    """
    Получает атрибут из объекта или словаря.
    :param obj: Объект модели или словарь
    :param attr: Атрибут, к которому нужно получить доступ
    :param model_class: Если obj - это словарь, модель, к которой он относится
    :return: Значение атрибута
    """
    if isinstance(obj, dict):
        # Если это словарь, то получаем значение по ключу
        return obj.get(attr)
    elif isinstance(obj, model_class):
        # Если это объект модели, то используем getattr
        return getattr(obj, attr, None)
    else:
        return None
