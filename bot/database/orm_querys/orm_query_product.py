import logging

from sqlalchemy.orm import selectinload

from utilit.seshe import async_cache

# Настройка логгер
logger = logging.getLogger(__name__)

from typing import Optional, Dict, Any, Sequence
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, exc
from database.models import Product, Category




async def orm_add_product(session: AsyncSession, data: Dict[str, Any]) -> Product:
    """
    Создает новый товар в базе данных с полной валидацией данных.

    Параметры:
        session: Асинхронная сессия БД
        data: Словарь с данными товара. Должен содержать:
            - name (str): Название товара
            - description (str): Описание
            - price (число): Цена
            - image (str): URL изображения
            - category (int): ID категории

    Возвращает:
        Product: Созданный объект товара

    Исключения:
        ValueError: При некорректных данных
        RuntimeError: При ошибках БД
    """
    logger.info("Попытка добавления нового товара")

    try:
        # Валидация обязательных полей
        required_fields = {'name', 'description', 'price', 'image', 'category'}
        if missing := required_fields - data.keys():
            raise ValueError(f"Отсутствуют обязательные поля: {missing}")

        # Проверка существования категории
        category_exists = await session.execute(
            select(Category.id).where(Category.id == int(data['category'])))
        if not category_exists.scalar():
            raise ValueError(f"Категория {data['category']} не существует")

        # Преобразование типов с обработкой ошибок
        try:
            price = Decimal(str(data['price'])).quantize(Decimal('0.01'))
            category_id = int(data['category'])
        except (ValueError, TypeError) as e:
            raise ValueError("Некорректные данные цены или категории") from e

        # Создание объекта
        product = Product(
            name=data['name'].strip(),
            description=data['description'].strip(),
            price=price,
            image=data['image'].strip(),
            category_id=category_id
        )

        async with session.begin():
            session.add(product)
            await session.flush()
            logger.info(f"Товар {product.id} создан: {product.name}")
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


@async_cache(ttl=300)
async def orm_get_products(
        session: AsyncSession,
        category_id: int,
        limit: int = 100,
        offset: int = 0
) -> Sequence[Product]:
    """
    Получает список товаров категории с пагинацией и кэшированием.

    Параметры:
        session: Асинхронная сессия БД
        category_id: ID категории
        limit: Максимальное количество товаров
        offset: Смещение выборки

    Возвращает:
        Sequence[Product]: Последовательность объектов Product

    Исключения:
        RuntimeError: При ошибках БД
    """
    logger.debug(f"Запрос товаров категории {category_id} [limit={limit}]")

    try:
        result = await session.execute(
            select(Product)
            .where(Product.category_id == category_id)
            .options(selectinload(Product.category))
            .order_by(Product.name)
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка получения товаров: {str(e)}")
        raise RuntimeError("Ошибка запроса данных") from e


async def orm_get_product(
        session: AsyncSession,
        product_id: int
) -> Optional[Product]:
    """
    Получает полную информацию о товаре по ID.

    Параметры:
        session: Асинхронная сессия БД
        product_id: Идентификатор товара

    Возвращает:
        Optional[Product]: Объект товара или None

    Исключения:
        RuntimeError: При ошибках БД
    """
    logger.debug(f"Запрос товара {product_id}")

    try:
        result = await session.execute(
            select(Product)
            .where(Product.id == product_id)
            .options(selectinload(Product.category))
        )
        return result.scalar_one_or_none()

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка получения товара {product_id}: {str(e)}")
        raise RuntimeError("Ошибка запроса товара") from e


async def orm_update_product(
        session: AsyncSession,
        product_id: int,
        data: Dict[str, Any]
) -> bool:
    """
    Обновляет данные товара. Возвращает True если обновление успешно.

    Параметры:
        session: Асинхронная сессия БД
        product_id: ID товара
        data: Словарь с новыми данными

    Возвращает:
        bool: Результат операции

    Исключения:
        ValueError: При некорректных данных
        RuntimeError: При ошибках БД
    """
    logger.info(f"Обновление товара {product_id}")

    try:
        updates = {}
        # Подготовка данных для обновления
        if 'name' in data:
            updates['name'] = str(data['name']).strip()
        if 'description' in data:
            updates['description'] = str(data['description']).strip()
        if 'price' in data:
            try:
                updates['price'] = Decimal(str(data['price'])).quantize(Decimal('0.01'))
            except (ValueError, TypeError) as e:
                raise ValueError("Некорректное значение цены") from e
        if 'image' in data:
            updates['image'] = str(data['image']).strip()
        if 'category' in data:
            try:
                updates['category_id'] = int(data['category'])
            except (ValueError, TypeError) as e:
                raise ValueError("Некорректный ID категории") from e

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
            return bool(result.scalar_one_or_none())

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка обновления товара {product_id}: {str(e)}")
        raise RuntimeError("Ошибка обновления данных") from e


async def orm_delete_product(session: AsyncSession, product_id: int) -> bool:
    """
    Удаляет товар по ID. Возвращает True если удаление успешно.

    Параметры:
        session: Асинхронная сессия БД
        product_id: ID товара

    Возвращает:
        bool: Результат операции

    Исключения:
        RuntimeError: При ошибках БД
    """
    logger.warning(f"Попытка удаления товара {product_id}")

    try:
        async with session.begin():
            result = await session.execute(
                delete(Product)
                .where(Product.id == product_id)
                .returning(Product.id)
            )
            return bool(result.scalar_one_or_none())

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка удаления товара {product_id}: {str(e)}")
        raise RuntimeError("Ошибка удаления товара") from e
