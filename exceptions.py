class StatusCode(Exception):
    """Ошибка, возникающая если статус отличается от 200."""


class EmptyListException(Exception):
    """Ошибка, возникающая при пустом списке домашек."""


class SendException(Exception):
    """Ошибка, возникающая при неудачной отправке сообщения."""


class GetApiException(Exception):
    """Ошибка, возникающая при отсутствии ответа от сервера."""
