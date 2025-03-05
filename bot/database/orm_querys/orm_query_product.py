import logging
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Product

# Настройка логгер
logger = logging.getLogger(__name__)


# Добавление нового товара
async def orm_add_product(session: AsyncSession, data: dict):
    """
    Добавляет новый товар в базу данных. Информация о товаре передается через словарь `data`.
    """
    logger.info(f"Добавление нового товара: {data['name']}")
    try:
        obj = Product(
            name=data["name"],
            description=data["description"],
            price=float(data["price"]),
            image=data["image"],
            category_id=int(data["category"]),
        )
        session.add(obj)
        await session.commit()
        logger.info(f"Товар '{data['name']}' успешно добавлен в категорию {data['category']}")
    except Exception as e:
        await session.rollback()
        logger.exception(f"Ошибка при добавлении товара: {str(e)}")
        raise


# Получение всех товаров определенной категории
async def orm_get_products(session: AsyncSession, category_id: int):
    """
    Возвращает список товаров в указанной категории.
    """
    logger.info(f"Запрос списка товаров для категории {category_id}")
    try:
        query = select(Product).where(Product.category_id == int(category_id))
        result = await session.execute(query)
        products = result.scalars().all()
        logger.info(f"Найдено {len(products)} товаров в категории {category_id}")
        return products
    except Exception as e:
        logger.exception(f"Ошибка при получении товаров категории {category_id}: {str(e)}")
        raise


# Получение информации о конкретном товаре
async def orm_get_product(session: AsyncSession, product_id: int):
    """
    Возвращает информацию о товаре по его ID.
    """
    logger.info(f"Запрос информации о товаре {product_id}")
    try:
        query = select(Product).where(Product.id == product_id)
        result = await session.execute(query)
        product = result.scalar()
        if product:
            logger.info(f"Товар {product_id} найден: {product.name}")
        else:
            logger.warning(f"Товар {product_id} не найден")
        return product
    except Exception as e:
        logger.exception(f"Ошибка при получении информации о товаре {product_id}: {str(e)}")
        raise


# Обновление информации о товаре
async def orm_update_product(session: AsyncSession, product_id: int, data: dict):
    """
    Обновляет информацию о товаре с заданным ID, используя данные из словаря `data`.
    """
    logger.info(f"Обновление товара {product_id}")
    try:
        query = (
            update(Product)
            .where(Product.id == product_id)
            .values(
                name=data["name"],
                description=data["description"],
                price=float(data["price"]),
                image=data["image"],
                category_id=int(data["category"]),
            )
        )
        await session.execute(query)
        await session.commit()
        logger.info(f"Товар {product_id} обновлен: {data['name']}")
    except Exception as e:
        await session.rollback()
        logger.exception(f"Ошибка при обновлении товара {product_id}: {str(e)}")
        raise


# Удаление товара
async def orm_delete_product(session: AsyncSession, product_id: int):
    """
    Удаляет товар из базы данных по его ID.
    """
    logger.info(f"Удаление товара {product_id}")
    try:
        query = delete(Product).where(Product.id == product_id)
        await session.execute(query)
        await session.commit()
        logger.info(f"Товар {product_id} успешно удален")
    except Exception as e:
        await session.rollback()
        logger.exception(f"Ошибка при удалении товара {product_id}: {str(e)}")
        raise
