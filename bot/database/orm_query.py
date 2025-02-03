from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Banner, Cart, Category, Product, User, Order, OrderItem


############### Работа с баннерами (информационными страницами) ###############

# Функция для добавления или изменения описания баннеров
async def orm_add_banner_description(session: AsyncSession, data: dict):
    """
    Проверяем существование записей в таблице Banner. Если записей нет, добавляем новые
    с описаниями из словаря `data`. Ключи словаря — имена пунктов (например, main, about),
    значения — их описание.
    """
    query = select(Banner)  # Проверяем существующие записи
    result = await session.execute(query)
    if result.first():  # Если записи уже существуют, ничего не делаем
        return
    # Добавляем новые баннеры
    session.add_all([Banner(name=name, description=description) for name, description in data.items()])
    await session.commit()


# Функция для изменения изображения и ссылки администратора у баннера
async def orm_change_banner_image(session: AsyncSession, name: str, image: str, admin_link: str | None = None):
    """
    Изменяет изображение и (опционально) ссылку администратора для баннера с заданным именем.
    """
    query = update(Banner).where(Banner.name == name).values(image=image, admin_link=admin_link)
    await session.execute(query)
    await session.commit()


# Функция для получения информации о баннере по его имени (странице)
async def orm_get_banner(session: AsyncSession, page: str):
    """
    Возвращает баннер для указанной страницы.
    """
    query = select(Banner).where(Banner.name == page)
    result = await session.execute(query)
    return result.scalar()


# Функция для получения всех информационных страниц или конкретной
async def orm_get_info_pages(session: AsyncSession, page: str | None = None):
    """
    Возвращает список информационных баннеров.
    Если `page` указан, возвращает только баннер для конкретной страницы.
    """
    query = select(Banner)
    if page:
        query = query.where(Banner.name == page)
    result = await session.execute(query)
    return result.scalars().all()


############################ Категории ######################################

# Получение всех категорий товаров
async def orm_get_categories(session: AsyncSession):
    """
    Возвращает список всех категорий в базе данных.
    """
    query = select(Category)
    result = await session.execute(query)
    return result.scalars().all()


# Создание новых категорий
async def orm_create_categories(session: AsyncSession, categories: list):
    """
    Добавляет новые категории. Если в таблице уже есть записи, ничего не происходит.
    """
    query = select(Category)
    result = await session.execute(query)
    if result.first():  # Проверяем, существуют ли категории
        return
    session.add_all([Category(name=name) for name in categories])
    await session.commit()


############ Админка: добавить/изменить/удалить товар ########################

# Добавление нового товара
async def orm_add_product(session: AsyncSession, data: dict):
    """
    Добавляет новый товар в базу данных. Информация о товаре передается через словарь `data`.
    """
    obj = Product(
        name=data["name"],
        description=data["description"],
        price=float(data["price"]),
        image=data["image"],
        category_id=int(data["category"]),
    )
    session.add(obj)
    await session.commit()


# Получение всех товаров определенной категории
async def orm_get_products(session: AsyncSession, category_id):
    """
    Возвращает список товаров в указанной категории.
    """
    query = select(Product).where(Product.category_id == int(category_id))
    result = await session.execute(query)
    return result.scalars().all()


# Получение информации о конкретном товаре
async def orm_get_product(session: AsyncSession, product_id: int):
    """
    Возвращает информацию о товаре по его ID.
    """
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    return result.scalar()


# Обновление информации о товаре
async def orm_update_product(session: AsyncSession, product_id: int, data):
    """
    Обновляет информацию о товаре с заданным ID, используя данные из словаря `data`.
    """
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


# Удаление товара
async def orm_delete_product(session: AsyncSession, product_id: int):
    """
    Удаляет товар из базы данных по его ID.
    """
    query = delete(Product).where(Product.id == product_id)
    await session.execute(query)
    await session.commit()


##################### Работа с пользователями #####################################

# Добавление пользователя в базу
async def orm_add_user(
        session: AsyncSession,
        user_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
):
    """
    Добавляет нового пользователя в базу данных, если его там еще нет.
    """
    query = select(User).where(User.user_id == user_id)  # Проверяем, существует ли пользователь
    result = await session.execute(query)
    if result.first() is None:  # Если пользователь не найден, добавляем
        session.add(
            User(user_id=user_id, first_name=first_name, last_name=last_name, phone=phone)
        )
        await session.commit()


######################## Работа с корзинами #######################################

# Добавление товара в корзину
async def orm_add_to_cart(session: AsyncSession, user_id: int, product_id: int):
    """
    Добавляет товар в корзину пользователя. Если товар уже есть в корзине,
    увеличивает его количество.
    """
    query = select(Cart).where(Cart.user_id == user_id,
                               Cart.product_id == product_id).options(joinedload(Cart.product))
    cart = await session.execute(query)
    cart = cart.scalar()
    if cart:  # Если товар уже в корзине, увеличиваем количество
        cart.quantity += 1
        await session.commit()
        return cart
    else:  # Иначе добавляем товар в корзину
        session.add(Cart(user_id=user_id, product_id=product_id, quantity=1))
        await session.commit()


# Получение корзины пользователя
async def orm_get_user_carts(session: AsyncSession, user_id):
    """
    Возвращает список всех товаров в корзине пользователя.
    """
    query = select(Cart).filter(Cart.user_id == user_id).options(joinedload(Cart.product))
    result = await session.execute(query)
    return result.scalars().all()


# Удаление товара из корзины
async def orm_delete_from_cart(session: AsyncSession, user_id: int, product_id: int):
    """
    Удаляет товар из корзины по ID пользователя и ID товара.
    """
    query = delete(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id)
    await session.execute(query)
    await session.commit()


# Уменьшение количества товара в корзине
async def orm_reduce_product_in_cart(session: AsyncSession, user_id: int, product_id: int):
    """
    Уменьшает количество товара в корзине. Если количество становится 0, удаляет товар.
    """
    query = select(Cart).where(Cart.user_id == user_id,
                               Cart.product_id == product_id)
    cart = await session.execute(query)
    cart = cart.scalar()

    if not cart:  # Если товара нет, ничего не делаем
        return
    if cart.quantity > 1:  # Уменьшаем количество
        cart.quantity -= 1
        await session.commit()
        return True
    else:  # Если количество меньше 1, удаляем товар
        await orm_delete_from_cart(session, user_id, product_id)
        await session.commit()
        return False


######################## Работа с заказами #######################################

# Создание заказа
async def orm_add_order(
        session: AsyncSession,
        user_id: int,
        total_price: float,
        items: list[dict],
        address: str | None = None,
        phone: str | None = None,
        status: str = "pending"
):
    """
    Создает новый заказ. Проверяет корректность данных и существование товаров.
    """
    # Проверяем структуру `items`
    if not isinstance(items, list):
        raise ValueError("items должен быть списком")

    for item in items:
        if not all(key in item for key in ("product_id", "quantity", "price")):
            raise ValueError("Каждый элемент items должен содержать product_id, quantity и price")

        if item["quantity"] < 1:
            raise ValueError(f"Некорректное количество для продукта {item['product_id']}")

        if item["price"] < 0:
            raise ValueError(f"Некорректная цена для продукта {item['product_id']}")

    # Проверяем существование товаров
    product_ids = [item["product_id"] for item in items]
    existing_products = await session.execute(select(Product.id).where(Product.id.in_(product_ids)))
    existing_ids = {row[0] for row in existing_products.all()}

    missing_ids = set(product_ids) - existing_ids
    if missing_ids:  # Если какой-то товар не существует, выбрасываем исключение
        raise ValueError(f"Товары с ID {missing_ids} не найдены")

    try:
        # Создаем заказ
        order = Order(
            user_id=user_id,
            total_price=total_price,
            status=status,
            address=address,
            phone=phone
        )
        session.add(order)
        await session.flush()  # Сохраняем изменения и получаем ID заказа

        # Добавляем элементы заказа
        for item in items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item["product_id"],
                quantity=item["quantity"],
                price=item["price"]
            )
            session.add(order_item)

        await session.commit()  # Подтверждаем изменения
        return order

    except Exception as e:
        await session.rollback()  # Если произошла ошибка, откатываем изменения
        raise RuntimeError(f"Ошибка при создании заказа: {str(e)}")


async def orm_create_order(session: AsyncSession, data: dict):
    order = Order(
        user_id=data["user_id"],
        total_price=data["total_price"]
    )
    session.add(order)
    await session.flush()
    return order

async def orm_add_order_items(session: AsyncSession, order_id: int, items: list):
    for item in items:
        order_item = OrderItem(
            order_id=order_id,
            product_id=item["product_id"],
            quantity=item["quantity"],
            price=item["price"]
        )
        session.add(order_item)
    await session.commit()


# Получение заказов пользователя
async def orm_get_user_orders(session: AsyncSession, user_id: int):
    """
    Возвращает список заказов пользователя.
    """
    query = (
        select(Order)
        .where(Order.user_id == user_id)
        .options(joinedload(Order.items))
        .order_by(Order.created.desc())  # Сортируем заказы по дате создания (последние выше)
    )
    result = await session.execute(query)
    return result.unique().scalars().all()


# Получение деталей конкретного заказа
async def orm_get_order_details(session: AsyncSession, order_id: int):
    """
    Возвращает данные заказа и связанные с ним товары.
    """
    query = (
        select(Order)
        .where(Order.id == order_id)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
    )
    result = await session.execute(query)
    return result.unique().scalar()


# Обновление статуса заказа
async def orm_update_order_status(session: AsyncSession, order_id: int, new_status: str):
    """
    Изменяет статус заказа.
    """
    query = (
        update(Order)
        .where(Order.id == order_id)
        .values(status=new_status)
    )
    await session.execute(query)
    await session.commit()


# Удаление заказа
async def orm_delete_order(session: AsyncSession, order_id: int):
    """
    Удаляет заказ из базы данных.
    """
    query = delete(Order).where(Order.id == order_id)
    await session.execute(query)
    await session.commit()
