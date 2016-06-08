How to write an underworlds client
==================================

This guide explains how to build underworlds application in Python.

It assumes that underworld is installed (otherwise, check `installation`).

General
~~~~~~~

The following simple snippet of code is a good starting point for many
underworlds Python applications:

.. code-block:: python
    :linenos:

    import logging; logger = logging.getLogger("underworlds.myapp")
    import underworlds

    # Define here the classes and functions you need
    # ...

    if __name__ == "__main__":

        logging.basicConfig(level=logging.INFO)

        # Manage command line options
        import argparse
        parser = argparse.ArgumentParser(description="My Cool App"))
        parser.add_argument("world", help="Underworlds world to monitor")
        args = parser.parse_args()


        with underworlds.Context("myapp") as ctx:

            world = ctx.worlds[args.world]

            # world.scene.nodes gives access to all the nodes present in this
            # world

            # world.scene.rootnode is the root node of the scene

            # world.timeline gives access to the world's timeline


Let see now one 'real world' example.

Implementing a filter
~~~~~~~~~~~~~~~~~~~~~

*Filters* are a common pattern in a underworlds-based system. We call a
*filter* an application that monitors a world A, processes somehow
its content, and generates a new world B which is a filtered version of
A.

One possible example is a physics-based filter: such a filter would read the
positions of various objects from a 'raw' world fed by the sensors. Because
perception routines are usually slightly inaccurate, some objects may be
detected as if they were *inside* others, or on the contrary flying in the air,
above their support. Using a physics engine, a physics-based filter would
correct these misdetections, and place the objects at stable locations. This
would result in a new world that one could call ``stable world``. This new world
could then be used as input for further processing by other reasonners,
planners, etc.

A possible implementation of a simpler filter (that would simply get flying
objects to 'drop' on their underlying support) could look like this:

.. code-block:: python
    :linenos:

    import logging; logger = logging.getLogger("underworlds.filter.flying")

    import underworlds
    from underworlds.types import *
    from underworlds.helpers.geometry import transformed_aabb

    def find_support(node, candidates):

        # left as an exercise for the reader!
        # (or check the link to the full source code below!)

    def filter(in_scene, out_scene):

        dynamic_objs = []

        for node in in_scene.nodes:
            if node.properties["physics"]:
                dynamic_objs.append(node)

        for obj in dynamic_objs:
            support, dt = find_support(obj, in_scene.nodes)
            if support:
                logger.info("%s should be on %s. Moving its center at %.2fm" % (obj.name, support.name, dt))

                # modify the position of the node in the 'out' world:
                node = out_scene.nodes[obj.id]
                node.transformation[2][3] = dt
                out_scene.nodes.update(node) # commit the changes to the underworlds network

            else:
                print("No support for %s! Leaving it alone." % d.name)


    if __name__ == "__main__":

        # Manage command line options
        import argparse
        parser = argparse.ArgumentParser(description='Move flying objects to rest position'))
        parser.add_argument("input", help="underworlds world to monitor")
        parser.add_argument("output", help="resulting underworlds world")
        args = parser.parse_args()

        with underworlds.Context("flying filter") as ctx:

            in_world = ctx.worlds[args.input]
            setup_physics(in_world.scene)

            out_world = ctx.worlds[args.output]

            # Fill in the 'out' world by copying the 'in' world and running
            # 'filter' a first time.

            # copy the 'in' scene onto the 'out' scene, overwriting previous
            # content
            out_world.copy_from(in_world)
            filter(in_world.scene, out_world.scene)

            # then, monitor the 'in' world for changes and update accordingly
            # the 'out' world.
            try:
                while True:

                    # wait until someting is modified in the world that
                    # we monitor
                    in_world.scene.waitforchanges()

                    # copy the 'in' scene onto the 'out' scene, overwriting previous
                    # content
                    out_world.copy_from(in_world)

                    filter(in_world.scene, out_world.scene)

            except KeyboardInterrupt:
                print("Bye bye")



You can see the complete source for this filter here: `flying\_filter.py
<https://github.com/severin-lemaignan/underworlds/tree/master/clients/flying_filter.py>`__
