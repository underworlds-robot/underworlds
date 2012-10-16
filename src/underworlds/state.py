class State():

    def __init__(self):
        pass

    def list_objects(self):
        """ Returns the list of objects contained in the state.

        Objects are either rigid bodies (ie, no joints, and hence only one
        frame) or complex bodies (ie, with a kinematic chain and hence 
        several frames, one per joint).
        """
        return []

    def list_frames(self):
        """ Returns the list of all frames known in this state.
        """
        return []
