import uuid
from random import randint, choice
import numpy

class Node(object):

    def __init__(self, id = None, name = None, value = None):

        self.id = id or str(uuid.uuid4())
        self.name = name or "".join([choice("abcdefghijklmnopqrst") for i in range(5)])
        self.value = numpy.matrix(value) if value else numpy.matrix([[randint(1,10), randint(1,10)],[randint(1,10), randint(1,10)]])

    def __repr__(self):
        return self.name + " " + str(self.value)

