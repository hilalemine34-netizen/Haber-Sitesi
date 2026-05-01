class BaseModel:

    def to_dict(self):
        return self.__dict__

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.__dict__}>"