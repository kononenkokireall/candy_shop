import math
import logging
from typing import Union, List, Any, Tuple

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    # Уровень логирования (например, DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Paginator:
    def __init__(
            self,
            array: Union[List[Any], Tuple[Any, ...]],
            page: int = 1,
            per_page: int = 1
    ) -> None:
        """
        Конструктор класса Paginator.

        Parameters:
            array (list | tuple): Список или кортеж данных для пагинации
            page (int): Текущая страница (по умолчанию 1)
            per_page (int): Количество элементов на странице (по умолчанию 1)
        """
        self.array = array
        self.per_page = per_page
        self.page = page
        self.len = len(self.array)  # Общее количество элементов
        self.pages = math.ceil(
            self.len / self.per_page)  # Общее количество страниц

        logger.info("Инициализация Paginator...")
        logger.debug(
            "Создан Paginator:"
            " всего элементов = %d, элементов на странице = %d, "
            "всего страниц = %d",
            self.len,
            self.per_page,
            self.pages,
        )

    def __get_slice(self) -> Union[List[Any], Tuple[Any, ...]]:
        """
        Приватный метод для вычисления диапазона данных на текущей странице.

        Returns:
            list | tuple: Срез данных для текущей страницы.
        """
        start = (self.page - 1) * self.per_page
        # Индекс начала текущей страницы
        stop = start + self.per_page  # Индекс конца текущей страницы
        logger.debug(
            "Получение данных для страницы %d (срез: %d:%d)",
            self.page, start, stop
        )
        return self.array[start:stop]

    def get_page(self) -> Union[List[Any], Tuple[Any, ...]]:
        """
        Получение данных текущей страницы.

        Returns:
            list | tuple: Данные текущей страницы.
        """
        page_items = self.__get_slice()  # Получаем срез данных
        logger.info("Текущая страница: %d", self.page)
        logger.debug("Данные страницы %d: %s",
                     self.page, page_items)
        return page_items

    def has_next(self) -> Union[int, bool]:
        """
        Проверка наличия следующей страницы.

        Returns:
            bool | int: Номер следующей страницы или False,
             если следующей страницы нет.
        """
        if self.page < self.pages:
            logger.debug("Следующая страница существует: %d",
                         self.page + 1)
            return self.page + 1
        logger.debug("Следующей страницы нет.")
        return False

    def has_previous(self) -> Union[int, bool]:
        """
        Проверка наличия предыдущей страницы.

        Returns:
            bool | int: Номер предыдущей страницы или False,
             если предыдущей страницы нет.
        """
        if self.page > 1:
            logger.debug("Предыдущая страница существует: %d",
                         self.page - 1)
            return self.page - 1
        logger.debug("Предыдущей страницы нет.")
        return False

    def get_next(self) -> Union[List[Any], Tuple[Any, ...]]:
        """
        Переход к следующей странице.

        Returns:
            list | tuple: Данные следующей страницы.

        Raises:
            IndexError: Если следующей страницы не существует.
        """
        if self.page < self.pages:
            self.page += 1
            logger.info("Переход на следующую страницу: %d",
                        self.page)
            return self.get_page()
        logger.error("Попытка перейти на несуществующую следующую страницу.")
        raise IndexError("Next page does not exist. Use has_next()"
                         " to check before.")

    def get_previous(self) -> Union[List[Any], Tuple[Any, ...]]:
        """
        Переход к предыдущей странице.

        Returns:
            list | tuple: Данные предыдущей страницы.

        Raises:
            IndexError: Если предыдущей страницы не существует.
        """
        if self.page > 1:
            self.page -= 1
            logger.info("Переход на предыдущую страницу: %d",
                        self.page)
            return self.__get_slice()
        logger.error("Попытка перейти на несуществующую предыдущую страницу.")
        raise IndexError(
            "Previous page does not exist. Use has_previous() to check before."
        )
