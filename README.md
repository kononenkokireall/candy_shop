## Настройка БД
Таблицы:
- `Banner`: Описание страниц (main, about, cart).
- `Product`: Товары с привязкой к категориям.
- `Cart`: Корзина пользователя.

## Пример запроса
```python
from database.orm_query import orm_get_products
products = await orm_get_products(session, category_id=1)