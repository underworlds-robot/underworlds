from underworlds.state import State

worlds = {}

def get_world(id):
    """Return a world by its ID. If the world does not exist, create it.

    :param string id: the identifier of the requested world
    :returns: a world or None if the world does not exist.
    """

    global worlds
    return worlds.setdefault(id, World())


class World:

    def __init__(self):
        self.state = State()

    def load(self, path):
        """Loads a Collada file in the world.

        The kinematic chains are added to the world's geometric state.
        The meshes are added to the meshes repository.

        A new 'load' event is also added the the world timeline.

        :param string path: the path (relative or absolute) to the Collada resource
        :todo: everything :-)

        """
        pass

    def get_state(self):
        return self.state
