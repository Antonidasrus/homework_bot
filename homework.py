import logging
import requests
import telegram
import time

from exceptions import (StatusCode, EmptyListException,
                        SendException, GetApiException)
from http import HTTPStatus
from typing import NoReturn
from config import (PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN,
                    RETRY_PERIOD, ENDPOINT, HOMEWORK_VERDICTS, HEADERS)

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s, %(funcName)s, %(levelno)s')


def check_tokens() -> bool:
    """Функция для проверки токенов."""
    return all([PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN])


def send_message(bot: telegram.Bot, message: str) -> None:
    """Функция отправки сообщения."""
    logging.debug('Начинаем отправку сообщения...')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception:
        logging.error('Не удалось отправить сообщение.')
        raise SendException('Не удалось отправить сообщение.')
    logging.debug('Сообщение отправлено.')


def get_api_answer(timestamp) -> list:
    """Функция для получения ответа от сервера."""
    logging.debug('Получаем новые статусы...')
    PAYLOAD = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(ENDPOINT,
                                         headers=HEADERS,
                                         params=PAYLOAD)
    except requests.RequestException:
        logging.error('Не удалось получить ответ от сервера.')
        raise GetApiException('Не удалось получить ответ от сервера.')

    if homework_statuses.status_code != HTTPStatus.OK:
        error_message = ('Ошибка при получении работ. Статус-код:'
                         f'{homework_statuses.status_code}')
        logging.error(error_message)
        raise StatusCode(error_message)
    return homework_statuses.json()


def check_response(response) -> None:
    """Функция для проверки полученного ответа."""
    if not isinstance(response, dict):
        logging.error('Должен возвращаться словарь dict')
        raise TypeError('Должен возвращаться словарь dict')
    if 'homeworks' not in response or 'current_date' not in response:
        logging.error('Отсутствуют некоторые обязательные поля')
        raise KeyError('Отсутствуют некоторые обязательные поля')
    if not isinstance(response.get('homeworks'), list):
        logging.error('homeworks не список')
        raise TypeError('homeworks не список')
    if not response.get('homeworks'):
        logging.error('Список домашек пуст')
        raise EmptyListException('Список домашек пуст')


def parse_status(homework) -> str:
    """Функция для вывода статуса домашки."""
    if 'homework_name' not in homework:
        logging.error('Домашки с таким названием не существует')
        raise KeyError('Домашки с таким названием не существует')
    homework_name = homework['homework_name']
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        logging.error('Статус домашки неизвестен')
        raise KeyError('Статус домашки неизвестен')
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main() -> NoReturn:
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Не хватает какого-то токена.')
        exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    previous_message = 0

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homeworks = response['homeworks']
            if not len(homeworks):
                logging.debug('Статус не изменился')
                continue
            for homework in homeworks:
                verdict_string = parse_status(homework)
                if not previous_message:
                    previous_message = verdict_string
                    send_message(bot, verdict_string)
                if verdict_string != previous_message:
                    send_message(bot, verdict_string)
                logging.debug(f'Отправлено сообщение: {verdict_string}')
        except Exception as e:
            message = f'Ошибка {e}'
            logging.error(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
