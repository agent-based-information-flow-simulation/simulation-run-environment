class ExternalServiceException(Exception):
    def __init__(self, status_code: int, body: str):
        super().__init__("\n".join([f"[status {status_code}]", body]))


class TranslatorException(ExternalServiceException):
    def __init__(self, status_code: int, body: str):
        super().__init__(status_code, body)


class GraphGeneratorException(ExternalServiceException):
    def __init__(self, status_code: int, body: str):
        super().__init__(status_code, body)


class SimulationCreatorException(ExternalServiceException):
    def __init__(self, status_code: int, body: str):
        super().__init__(status_code, body)


class DataProcessorException(ExternalServiceException):
    def __init__(self, status_code: int, body: str):
        super().__init__(status_code, body)
