import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from sqlalchemy.ext.asyncio import async_sessionmaker

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования - INFO (можно сменить на DEBUG, если нужно больше деталей)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)  # Создаем лог для текущего модуля


class DataBaseSession(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        """
        Middleware класс DataBaseSession.

        Parameters:
            session_pool (async_session maker): Пул асинхронных сессий SQLAlchemy.
        """
        self.session_pool = session_pool
        logger.info("Инициализирован DataBaseSession middleware с переданным session_pool.")

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        """
        Перехватчик событий, вызываемый для каждого входящего события.

        Parameters:
            handler (Callable): Функция-обработчик события.
            event (TelegramObject): Входящее событие Telegram.
            data (Dict[str, Any]): Контекст данных, переданный в обработчик.

        Returns:
            Any: Результат работы обработчика.
        """
        logger.debug("Обработка события: %s", event)

        # Создаём асинхронную сессию:
        async with self.session_pool() as session:
            try:
                logger.info("Создана новая асинхронная сессия работы с базой данных.")

                # Добавляем сессию в контекст данных
                data['session'] = session

                # Вызываем следующий обработчик в цепочке с обновлёнными данными
                result = await handler(event, data)

                logger.info("Событие обработано успешно: %s", event)
                return result
            except Exception as e:
                # Лог ошибки, если что-то пошло не так
                logger.error("Ошибка при обработке события: %s. Детали: %s", event, e)
                raise  # Пробрасываем исключение дальше, чтобы оно могло быть обработано
            finally:
                logger.info("Асинхронная сессия была завершена.")
