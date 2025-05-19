import logging
from decimal import Decimal
from typing import Optional, Dict, Any, Sequence

# Импорт функций для создания, выборки, обновления и удаления данных из БД
from sqlalchemy import select, update, delete, exc
# Импорт асинхронной сессии для работы с базой данных
from sqlalchemy.ext.asyncio import AsyncSession
# Опции для пред загрузки связанных объектов
from sqlalchemy.orm import selectinload

# Импорт моделей, используемых в запросах
from database.models import Product, Category, Cart

# Настройка логгера для модуля
logger = logging.getLogger(__name__)


# ======================== РАБОТА С ТОВАРАМИ (CRUD) ========================

async def orm_add_product(
        session: AsyncSession,
        data: Dict[str, Any]
) -> Product:
    """
    Создает новый товар в базе данных с полной валидацией данных.

    Параметры:
      - session: Асинхронная сессия для работы с БД
      - data: Словарь с данными товара (должен содержать все обязательные поля)

    Возвращает:
      - Объект созданного товара Product

    Исключения:
      - ValueError: При отсутствии полей/некорректных данных
      - RuntimeError: При ошибках работы с БД
      - RuntimeError: Внутренние необработанные ошибки
    """
    logger.info("Попытка добавления нового товара")

    try:
        # Валидация наличия обязательных полей
        required_fields = {"name", "description", "price", "image", "category"}
        if missing := required_fields - data.keys():
            raise ValueError(f"Отсутствуют обязательные поля: {missing}")

        # Проверка существования категории в БД
        category_exists = await session.execute(
            select(Category.id).where(Category.id == int(data["category"]))
        )
        if not category_exists.scalar():
            raise ValueError(f"Категория {data['category']} не существует")

        # Преобразование и валидация типов данных
        try:
            # Форматирование цены до двух знаков после запятой
            price = Decimal(str(data["price"])).quantize(Decimal("0.01"))
            category_id = int(data["category"])
        except (ValueError, TypeError) as e:
            raise ValueError("Некорректные данные цены или категории") from e

        # Создание объекта товара
        product = Product(
            name=data["name"].strip(),
            description=data["description"].strip(),
            price=price,
            image=data["image"].strip(),
            category_id=category_id,
        )

        # Сохранение в БД
        session.add(product)
        await session.flush()  # Принудительный flush для получения ID
        await session.commit()

        logger.info(f"Товар {product.id} создан: {product.name}")
        return product

    except exc.SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Ошибка БД при добавлении товара: {str(e)}")
        raise RuntimeError("Ошибка создания товара") from e
    except ValueError as e:
        logger.warning(f"Некорректные данные: {str(e)}")
        raise
    except Exception as e:
        await session.rollback()
        logger.exception("Неожиданная ошибка при добавлении товара")
        raise RuntimeError("Внутренняя ошибка сервера") from e


async def orm_get_products(
        session: AsyncSession,
        category_id: int,
        limit: int = 100,
        offset: int = 0
) -> Sequence[Product]:
    """
    Получает список товаров указанной категории с пагинацией.

    Параметры:
      - session: Асинхронная сессия БД
      - category_id: ID категории для фильтрации
      - limit: Максимальное количество записей (по умолчанию 100)
      - offset: Смещение для пагинации (по умолчанию 0)

    Возвращает:
      - Последовательность объектов Product

    Исключения:
      - ValueError: Если категория не найдена
      - RuntimeError: При ошибках запроса к БД
    """
    logger.debug(f"Запрос товаров категории {category_id}")

    # Проверка существования категории
    category_exists = await session.execute(
        select(Category.id).where(Category.id == category_id)
    )
    if not category_exists.scalar():
        raise ValueError(f"Категория {category_id} не найдена")

    try:
        # Формирование запроса с пагинацией и предзагрузкой категорий
        query = (
            select(Product)
            .where(Product.category_id == category_id)
            .options(
                selectinload(Product.category))  # Жадная загрузка категории
            .order_by(Product.name)  # Сортировка по имени
            .limit(limit)  # Ограничение количества
            .offset(offset)  # Смещение
        )

        result = await session.execute(query)
        return result.scalars().all()

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка получения товаров: {str(e)}")
        raise RuntimeError("Ошибка запроса данных") from e


async def orm_get_product(
        session: AsyncSession,
        product_id: int
) -> Optional[Product]:
    """
    Получает полную информацию о товаре по его ID.

    Параметры:
      - session: Асинхронная сессия БД
      - product_id: Идентификатор товара

    Возвращает:
      - Product: если товар найден
      - None: если товар не существует

    Исключения:
      - RuntimeError: При ошибках выполнения запроса
    """
    logger.debug(f"Запрос товара {product_id}")

    try:
        result = await session.execute(
            select(Product)
            .where(Product.id == product_id)
            .options(selectinload(Product.category))
            # Загрузка связанной категории
        )
        return result.scalar_one_or_none()  # Одна запись или None

    except exc.SQLAlchemyError as e:
        logger.error(f"Ошибка получения товара {product_id}: {str(e)}")
        raise RuntimeError("Ошибка запроса товара") from e


async def orm_update_product(
        session: AsyncSession,
        product_id: int,
        data: Dict[str, Any]
) -> bool:
    """
    Обновляет данные товара по его ID.

    Параметры:
      - session: Асинхронная сессия БД
      - product_id: ID обновляемого товара
      - data: Словарь с новыми данными (только изменяемые поля)

    Возвращает:
      - True: если обновление прошло успешно
      - False: если товар не найден или нет изменений

    Исключения:
      - ValueError: При некорректных данных
      - RuntimeError: При ошибках БД
    """
    logger.info(f"Обновление товара {product_id}")

    try:
        updates: Dict[str, Any] = {}

        # Подготовка данных для обновления
        if "name" in data:
            updates["name"] = str(data["name"]).strip()
        if "description" in data:
            updates["description"] = str(data["description"]).strip()
        if "price" in data:
            try:
                updates["price"] = Decimal(str(data["price"])).quantize(
                    Decimal("0.01"))
            except (ValueError, TypeError) as e:
                raise ValueError("Некорректное значение цены") from e
        if "image" in data:
            updates["image"] = str(data["image"]).strip()
        if "category" in data:
            try:
                updates["category_id"] = int(data["category"])
            except (ValueError, TypeError) as e:
                raise ValueError("Некорректный ID категории") from e

        # Проверка наличия изменений
        if not updates:
            logger.warning("Пустой запрос на обновление")
            return False

        # Выполнение запроса UPDATE с возвратом ID
        result = await session.execute(
            update(Product)
            .where(Product.id == product_id)
            .values(**updates)
            .returning(Product.id)  # Возврат ID для проверки успешности
        )

        await session.commit()
        return bool(result.scalar_one_or_none())  # True если запись обновлена

    except exc.SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Ошибка обновления товара {product_id}: {str(e)}")
        raise RuntimeError("Ошибка обновления данных") from e


async def orm_delete_product(
        session: AsyncSession,
        product_id: int
) -> bool:
    """
    Удаляет товар по его ID.

    Параметры:
      - session: Асинхронная сессия БД
      - product_id: ID удаляемого товара

    Возвращает:
      - True: если товар удален
      - False: если товар не найден

    Исключения:
      - RuntimeError: При ошибках работы с БД
    """
    logger.warning(f"Попытка удаления товара {product_id}")

    try:
        # Удаление с возвратом ID для проверки успешности
        result = await session.execute(
            delete(Product)
            .where(Product.id == product_id)
            .returning(Product.id)
        )
        await session.commit()
        return bool(result.scalar_one_or_none())

    except exc.SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Ошибка удаления товара {product_id}: {str(e)}")
        raise RuntimeError("Ошибка удаления товара") from e
