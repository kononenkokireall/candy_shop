import logging
from decimal import Decimal
from typing import Optional, Dict, Any, Sequence

# Импорт функций для создания, выборки, обновления и удаления данных из БД
from sqlalchemy import select, update, delete, exc

# Импорт асинхронной сессии для работы с базой данных
from sqlalchemy.ext.asyncio import AsyncSession

# Опции для пред загрузки связанных объектов
from sqlalchemy.orm import selectinload

from cache.decorators import cached
from cache.invalidator import CacheInvalidator
# Импорт моделей, используемых в запросах
from database.models import Product, Category, Cart

# Настройка логгера для модуля
logger = logging.getLogger(__name__)


# Функция Создает новый товар в базе данных с полной валидацией данных.
async def orm_add_product(
        session: AsyncSession,
        data: Dict[str, Any]
) -> Product:
    """
    Создает новый товар в базе данных с полной валидацией данных.

    Параметры:
      - session: Асинхронная сессия БД.
      - data: Словарь с данными товара. Должен содержать следующие ключи:
          • name (str): Название товара.
          • description (str): Описание товара.
          • price (число): Цена товара.
          • image (str): URL изображения товара.
          • category (int): ID категории, к которой принадлежит товар.

    Возвращает:
      - Product: Созданный объект товара.

    Исключения:
      - ValueError: Если отсутствуют обязательные поля или данные некорректны.
      - RuntimeError: Если возникает ошибка
       при выполнении запросов к базе данных.
    """
    logger.info("Попытка добавления нового товара")

    try:
        # Валидация: проверяем наличие всех обязательных полей
        required_fields = {"name", "description", "price", "image", "category"}
        if missing := required_fields - data.keys():
            raise ValueError(f"Отсутствуют обязательные поля: {missing}")

        # Проверяем, существует ли категория с указанным ID
        category_exists = await session.execute(
            select(Category.id).where(Category.id == int(data["category"]))
        )
        if not category_exists.scalar():
            raise ValueError(f"Категория {data['category']} не существует")

        # Преобразуем цену и ID категории в корректные типы
        try:
            price = Decimal(str(data["price"])).quantize(Decimal("0.01"))
            category_id = int(data["category"])
        except (ValueError, TypeError) as e:
            raise ValueError("Некорректные данные цены или категории") from e

        # Создаем объект товара с очищенными значениями
        product = Product(
            name=data["name"].strip(),
            description=data["description"].strip(),
            price=price,
            image=data["image"].strip(),
            category_id=category_id,
        )

        # Открываем транзакцию для добавления товара
        async with session.begin():
            session.add(product)
            # Выполняем flush, чтобы получить
            # сгенерированный ID товара до коммит
            await session.flush()
            logger.info(f"Товар {product.id} создан: {product.name}")
            # await CacheInvalidator.invalidate_by_pattern("products:*")
            return product

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка БД при добавлении товара: {str(e)}")
        raise RuntimeError("Ошибка создания товара") from e
    except ValueError as e:
        logger.warning(f"Некорректные данные: {str(e)}")
        raise
    except Exception as e:
        logger.exception("Неожиданная ошибка при добавлении товара")
        raise RuntimeError("Внутренняя ошибка сервера") from e


# Функция Получает список товаров определенной категории с поддержкой пагинации.
@cached("products:category:{category_id}:limit:{limit}:offset:{offset}",
        ttl=3600, model=Product)
async def orm_get_products(
        session: AsyncSession,
        category_id: int,
        limit: int = 100,
        offset: int = 0
) -> Sequence[Product]:
    logger.debug(f"Запрос товаров категории {category_id}")

    # Проверка существования категории
    category_exists = await session.execute(
        select(Category.id).where(Category.id == category_id)
        # Исправлено: закрывающая скобка
    )
    if not category_exists.scalar():
        raise ValueError(f"Категория {category_id} не найдена")

    try:
        # Формируем запрос с правильным синтаксисом
        query = (
            select(Product)
            .where(Product.category_id == category_id)
            .options(selectinload(Product.category))
            .order_by(Product.name)
            .limit(limit)
            .offset(offset)
        )

        result = await session.execute(query)
        return result.scalars().all()

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка получения товаров: {str(e)}")
        raise RuntimeError("Ошибка запроса данных") from e


# Функция Получает полную информацию о товаре по его ID.
@cached("product:{product_id}", ttl=3600, model=Product)
async def orm_get_product(
        session: AsyncSession,
        product_id: int
) -> Optional[Product]:
    """
    Получает полную информацию о товаре по его ID.

    Параметры:
      - session: Асинхронная сессия БД.
      - product_id: Идентификатор товара.

    Возвращает:
      - Optional[Product]: Объект товара, если найден, иначе None.

    Исключения:
      - RuntimeError: Если возникает ошибка при выполнении запроса.
    """
    logger.debug(f"Запрос товара {product_id}")

    try:
        result = await session.execute(
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.category)
            )  # Пред загрузка данных о категории товара
        )
        return result.scalar_one_or_none()

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка получения товара {product_id}: {str(e)}")
        raise RuntimeError("Ошибка запроса товара") from e


# Функция Обновляет данные товара по его ID с использованием переданных данных.
async def orm_update_product(
        session: AsyncSession,
        product_id: int,
        data: Dict[str, Any]
) -> bool:
    """
    Обновляет данные товара по его ID с использованием переданных данных.

    Параметры:
      - session: Асинхронная сессия БД.
      - product_id: ID товара, который необходимо обновить.
      - data: Словарь с новыми данными. Возможные ключи:
            • name
            • description
            • price
            • image
            • category

    Возвращает:
      - bool: True, если обновление прошло успешно, иначе False.

    Исключения:
      - ValueError: Если переданы некорректные данные.
      - RuntimeError: При ошибках работы с БД.
    """
    logger.info(f"Обновление товара {product_id}")

    try:
        updates: Dict[str, Any] = {}
        # Если поле 'name' присутствует,
        # очищаем строку и добавляем в обновления
        if "name" in data:
            updates["name"] = str(data["name"]).strip()
        # Если поле 'description' присутствует, очищаем и добавляем
        if "description" in data:
            updates["description"] = str(data["description"]).strip()
        # Если поле 'price' присутствует, пытаемся преобразовать его в Decimal
        if "price" in data:
            try:
                updates["price"] = (Decimal(str(data["price"]))
                                    .quantize(Decimal("0.01")))
            except (ValueError, TypeError) as e:
                raise ValueError("Некорректное значение цены") from e
        # Если поле 'image' присутствует, очищаем строку
        if "image" in data:
            updates["image"] = str(data["image"]).strip()
        # Если поле 'category' присутствует, преобразуем его в целое число
        if "category" in data:
            try:
                updates["category_id"] = int(data["category"])
            except (ValueError, TypeError) as e:
                raise ValueError("Некорректный ID категории") from e

        # Если нет никаких обновлений, логируем предупреждение
        # и возвращаем False
        if not updates:
            logger.warning("Пустой запрос на обновление")
            return False

        async with session.begin():
            result = await session.execute(
                update(Product)
                .where(Product.id == product_id)
                .values(**updates)
                .returning(Product.id)
            )
            await CacheInvalidator.invalidate([
                f"product:{product_id}",
                "products:*"
            ])
            await _invalidate_carts_with_product(session, product_id)
            # Если возвращается ID обновленного товара, операция успешна
            return bool(result.scalar_one_or_none())

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка обновления товара {product_id}: {str(e)}")
        raise RuntimeError("Ошибка обновления данных") from e


# Функция Удаляет товар по его ID.
async def orm_delete_product(
        session: AsyncSession,
        product_id: int
) -> bool:
    """
    Удаляет товар по его ID.

    Параметры:
      - session: Асинхронная сессия БД.
      - product_id: ID товара для удаления.

    Возвращает:
      - bool: True, если удаление прошло успешно, иначе False.

    Исключения:
      - RuntimeError: Если возникает ошибка при удалении товара.
    """
    logger.warning(f"Попытка удаления товара {product_id}")

    try:
        async with session.begin():
            result = await session.execute(
                delete(Product).where(Product.id == product_id)
                .returning(Product.id)
            )
            await CacheInvalidator.invalidate([
                f"product:{product_id}",
                "products:*"
            ])
            await _invalidate_carts_with_product(session, product_id)
            return bool(result.scalar_one_or_none())

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка удаления товара {product_id}: {str(e)}")
        raise RuntimeError("Ошибка удаления товара") from e


async def _invalidate_carts_with_product(
        session: AsyncSession,
        product_id: int
) -> None:
    """
    Инвалидирует корзины всех пользователей, у которых есть данный товар.

    Параметры:
      - session: Асинхронная сессия БД.
      - product_id: ID товара.
    """
    logger.info(f"Инвалидация корзин с товаром {product_id}")
    try:
        result = await session.execute(
            select(Cart.user_id)
            .where(Cart.product_id == product_id)
            .distinct()
        )
        user_ids = [row[0] for row in result.all()]
        if user_ids:
            logger.info(f"Найдены пользователи для инвалидации: {user_ids}")
            await CacheInvalidator.invalidate([
                f"cart:{user_id}" for user_id in user_ids
            ])
        else:
            logger.info(f"Нет пользователей с товаром {product_id}")
    except Exception as e:
        logger.warning(f"Ошибка инвалидации корзин: {str(e)}")
