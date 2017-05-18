import underworlds

with underworlds.Context("tablet_interface") as ctx:
    world = ctx.worlds["base"]

    # create a new node
    childnode = underwords.Node("child", type=underwords.types.CAMERA)
    # parent it to the rootnode (or any other node if you prefer)
    childnode.parent = world.scene.rootnode
    # set its pose
    childnode.transformation([[1,0,0,x], [0,1,0,y], [0,0,1,z],[0,0,0,1]])

    # if you do not provide any mesh, you might want to provide manually the boundingbox
    childnode.aabb([[x1,y1,z1], [x2,y2,z2]])

    # then, propagate the change:
    world.scene.nodes.update(childnode)

    #### Accessing existing nodes

    node = None
    nodes = world.scene.nodebyname("name")
    if nodes:
        node = nodes[0]

    node.transformation[0,3] = x
    node.transformation[1,3] = y
    node.transformation[2,3] = z
    
    # or...
    node.transformation([[1,0,0,x], [0,1,0,y], [0,0,1,z],[0,0,0,1]])


    # then, propagate the change:
    world.scene.nodes.update(node)

