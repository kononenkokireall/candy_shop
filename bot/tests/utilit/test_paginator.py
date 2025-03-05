# Тесты инициализации
import math
from unittest.mock import patch

import pytest

from utilit.paginator import Paginator


def test_paginator_init():
    data = [1, 2, 3, 4, 5]
    paginator = Paginator(data, page=1, per_page=2)
    assert paginator.pages == math.ceil(5 / 2)
    assert paginator.page == 1
    assert paginator.per_page == 2


def test_paginator_init_empty_data():
    paginator = Paginator([], per_page=3)
    assert paginator.pages == 0
    assert paginator.len == 0


def test_paginator_init_invalid_page():
    # Страница автоматически не корректируется, тестируем входные значения
    paginator = Paginator([1, 2, 3], page=0)
    assert paginator.page == 0  # Возможный баг: страница не должна быть < 1
    assert paginator.pages == 3


# Тесты метода get_page()
def test_get_page():
    data = [1, 2, 3, 4, 5]
    paginator = Paginator(data, page=1, per_page=2)
    assert paginator.get_page() == [1, 2]

    paginator.page = 3
    assert paginator.get_page() == [5]  # Последняя страница с одним элементом

    paginator.page = 4
    assert paginator.get_page() == []  # Пустой срез при page > pages


# Тесты has_next() и has_previous()
def test_has_next():
    paginator = Paginator([1, 2, 3, 4, 5], page=1, per_page=2)
    assert paginator.has_next() == 2

    paginator.page = 3
    assert paginator.has_next() is False


def test_has_previous():
    paginator = Paginator([1, 2, 3, 4, 5], page=2, per_page=2)
    assert paginator.has_previous() == 1

    paginator.page = 1
    assert paginator.has_previous() is False


# Тесты переходов между страницами
def test_get_next():
    paginator = Paginator([1, 2, 3, 4, 5], page=1, per_page=2)
    assert paginator.get_next() == [3, 4]
    assert paginator.page == 2

    paginator.page = 3
    with pytest.raises(IndexError):
        paginator.get_next()


def test_get_previous():
    paginator = Paginator([1, 2, 3, 4, 5], page=2, per_page=2)
    assert paginator.get_previous() == [1, 2]
    assert paginator.page == 1

    paginator.page = 1
    with pytest.raises(IndexError):
        paginator.get_previous()


# Тест логирования (используем моки)
@patch("your_module.logger")  # Замените на реальный путь к logger
def test_paginator_logging(mock_logger):
    data = [1, 2, 3]
    Paginator(data, page=1, per_page=1)

    # Проверка вызова logger.info
    mock_logger.info.assert_called_with("Инициализация Paginator...")

    # Проверка вызова logger.debug с параметрами
    expected_debug_msg = (
        "Создан Paginator: всего элементов = 3, элементов на странице = 1, всего страниц = 3"
    )
    mock_logger.debug.assert_called_with(
        "Создан Paginator: всего элементов = %%d, элементов на странице = %%d, всего страниц = %%d",
        3,
        1,
        3,
    )
