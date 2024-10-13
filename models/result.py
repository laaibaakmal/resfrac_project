class Result:
    isSuccess: bool
    message: str

    def __init__(self, isSuccess, message):
        self.isSuccess = isSuccess
        self.message = message
