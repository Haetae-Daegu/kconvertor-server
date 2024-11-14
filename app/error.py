class APIError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(self.message)

    def to_response(self):
        return {"code": self.code, "message": self.message}, self.code
