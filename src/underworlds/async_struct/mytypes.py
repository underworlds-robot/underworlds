import uuid
from random import randint, choice
import numpy
import copy, json


class Node(object):

    def __init__(self):

        self.id = str(uuid.uuid4())
        self.name = "".join([choice("abcdefghijklmnopqrst") for i in range(5)])
        self.value = [[randint(1,10), randint(1,10)],[randint(1,10), randint(1,10)]]

    def __repr__(self):
        return self.name + " " + str(self.value)

    def serialize(self):
        #d = copy.copy(self.__dict__)
        #d["value"] = d["value"].tolist()
        #return json.dumps(d)
        return json.dumps(self.__dict__)

    @staticmethod
    def deserialize(json):
        n = Node()
        data = json.loads(json)

        for key, value in data.items():
            if hasattr(n, key):
                setattr(n, key, value)

