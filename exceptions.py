class StatusCode(Exception):
    """Ошибка, возникающая если статус отличается от 200."""
    pass


class EmptyListException(Exception):
    """Ошибка, возникающая при пустом списке домашек."""
    pass


class SendException(Exception):
    """Ошибка, возникающая при неудачной отправке сообщения."""
    pass


class GetApiException(Exception):
    """Ошибка, возникающая при отсутствии ответа от сервера."""
    pass
