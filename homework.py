import os
import logging
import requests
import telegram

import time
from dotenv import load_dotenv
from exceptions import StatusCode, EmptyListException, SendException

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logger = logging.getLogger(__name__)


def check_tokens():
    """Функция для проверки токенов."""
    return all([PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN])


def send_message(bot, message):
    """Функция отправки сообщения."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение отправлено.')
    except SendException:
        logging.error('Не удалось отправить сообщение.')


def get_api_answer(timestamp):
    """Функция для получения ответа от сервера."""
    PAYLOAD = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(ENDPOINT,
                                         headers=HEADERS,
                                         params=PAYLOAD)
    except requests.RequestException:
        logging.error('Не удалось получить ответ от сервера.')

    if homework_statuses.status_code != 200:
        logging.error
        raise StatusCode('Ответ от сервера отличный от 200.')
    return homework_statuses.json()


def check_response(response):
    """Функция для проверки полученного ответа."""
    if type(response) is not dict:
        logging.error('Должен возвращаться словарь dict')
        raise TypeError('Должен возвращаться словарь dict')
    if 'homeworks' not in response or 'current_date' not in response:
        logging.error('Отсутствуют некоторые обязательные поля')
        raise KeyError('Отсутствуют некоторые обязательные поля')
    if type(response.get('homeworks')) is not list:
        logging.error('homeworks не список')
        raise TypeError('homeworks не список')
    if len(response.get('homeworks')) == 0:
        logging.error('Список домашек пуст')
        raise EmptyListException


def parse_status(homework):
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


def main():
    """Основная логика работы бота."""

    if not check_tokens():
        logging.critical('Не хватает какого-то токена.')
        exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

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
                send_message(bot, verdict_string)
                logging.debug(f'Отправлено сообщение: {verdict_string}')
        except Exception:
            message = 'Ошибка'
            logging.error(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
