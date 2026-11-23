class AppException(Exception):
    """Base for errors that map to an HTTP response of {"detail": message}."""

    status_code = 500

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFound(AppException):
    """Resource does not exist."""

    status_code = 404
