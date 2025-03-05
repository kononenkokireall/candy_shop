from aiogram.fsm.state import State, StatesGroup
from states.states import OrderProcess, AddBanner

def test_order_process_structure():
    # Проверяем, что OrderProcess является подклассом StatesGroup
    assert issubclass(OrderProcess, StatesGroup)

    # Проверяем наличие всех ожидаемых состояний
    expected_states = ['NAME', 'DESCRIPTION', 'CATEGORY', 'PRICE', 'ADD_IMAGES']
    for state_name in expected_states:
        assert hasattr(OrderProcess, state_name)
        state = getattr(OrderProcess, state_name)
        assert isinstance(state, State)

    # Проверяем дополнительные атрибуты
    assert hasattr(OrderProcess, 'product_for_change')
    assert OrderProcess.product_for_change is None

    # Проверяем тексты для состояний
    expected_texts = {
        'OrderProcess:NAME': 'Введите название заново:',
        'OrderProcess:DESCRIPTION': 'Введите описание заново:',
        'OrderProcess:PRICE': 'Введите стоимость заново:',
        'OrderProcess:ADD_IMAGES': 'Добавьте изображение меньше размером:',
    }
    assert OrderProcess.TEXTS == expected_texts

def test_add_banner_structure():
    # Проверяем структуру AddBanner
    assert issubclass(AddBanner, StatesGroup)
    assert hasattr(AddBanner, 'IMAGE')
    assert isinstance(AddBanner.IMAGE, State)

def test_state_group_inheritance():
    # Проверка наследования и инициализации состояний
    assert OrderProcess.__name__ in OrderProcess.NAME.state.group
    assert AddBanner.__name__ in AddBanner.IMAGE.state.group

def test_product_for_change_assignment():
    # Проверка возможности изменения product_for_change
    test_product = {'id': 1, 'name': 'Test Product'}
    OrderProcess.product_for_change = test_product
    assert OrderProcess.product_for_change == test_product
    OrderProcess.product_for_change = None  # Возвращаем исходное состояние