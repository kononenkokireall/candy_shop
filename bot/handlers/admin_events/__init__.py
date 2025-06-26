# routers/admin/__init__.py
from .admin_main import admin_router_root
from .banners import banners_router
from .base import menu_keyboard_router  # ← root-router
from .category import category_router
from .products import products_router

# «Вклеиваем» дочерние роутеры
#admin_router_root.include_router(admin_router_root)
admin_router_root.include_router(menu_keyboard_router)
admin_router_root.include_router(products_router)
admin_router_root.include_router(banners_router)
admin_router_root.include_router(category_router)

# для «from routers.admin import admin_router»
__all__ = ["admin_router_root"]