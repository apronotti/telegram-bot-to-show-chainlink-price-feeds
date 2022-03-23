import json

class Dict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

class Configuration():

    @staticmethod
    def __load__(data):
        result = None
        if isinstance(data, dict):
            result = Configuration.load_dict(data)
        else:
            result = data
        return result

    @staticmethod
    def load_dict(data: dict):
        result = Dict()
        for key, value in data.items():
            result[key] = Configuration.__load__(value)
        return result

    @staticmethod
    def load_json(path: str):
        with open(path, "r") as file:
            result = Configuration.__load__(json.loads(file.read()))
        return result
