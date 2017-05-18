import logging; logger = logging.getLogger("underworlds.myapp")
import underworlds

# Define here the classes and functions you need
# ...

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    # Manage command line options
    import argparse
    parser = argparse.ArgumentParser(description="My Cool App")
    parser.add_argument("world", help="Underworlds world to monitor")
    args = parser.parse_args()


    with underworlds.Context("myapp") as ctx:

        world = ctx.worlds[args.world]

        # world.scene.nodes gives access to all the nodes present in this
        # world
        for node in world.scene.nodes:
            # the 4x4 transformation matrix, relative to the parent
            transformation = node.transformation 
            x,y,z = transformation[0:3, 3] # last column contains translation

            print("Node %s (id: %s) is at (%.2fm, %.2fm, %.2fm) from \
                   its parent %s" % (node, node.id, x, y, z, node.parent))


        # world.scene.rootnode is the root node of the scene
        print("The root node is %s" % world.scene.rootnode)
        print("It has %d children" % len(world.scene.rootnode.children))

