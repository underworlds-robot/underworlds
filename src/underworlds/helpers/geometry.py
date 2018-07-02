import numpy
from numpy import linalg

import logging; logger = logging.getLogger("underworlds.helpers.geometry")

from ..types import MESH
from functools import reduce

def transform(vector3, matrix4x4):
    """ Apply a transformation matrix on a 3D vector.

    :param vector3: a numpy array with 3 elements
    :param matrix4x4: a numpy 4x4 matrix
    """
    return numpy.dot(matrix4x4, numpy.append(vector3, 1.))

def get_scene_bounding_box(scene):
    """
    Returns the axis-aligned bounding box (AABB) of a whole scene,
    or None if the scene is empty.
    """
    bb_min = [1e10, 1e10, 1e10] # x,y,z
    bb_max = [-1e10, -1e10, -1e10] # x,y,z

    if not scene.rootnode.children:
        logger.warning("rootnode has no children! The scene is probably empty.")
        return None, None

    return _compute_bounding_box_for_node(scene.nodes, scene.rootnode, bb_min, bb_max, linalg.inv(scene.rootnode.transformation))

def _compute_bounding_box_for_node(nodes, node, bb_min, bb_max, transformation):
    
    if node.type == MESH and "aabb" in node.properties:
        x1,y1,z1,x2,y2,z2 = node.properties["aabb"]
        for v in ((x1,y1,z1), (x2,y2,z2)):
            v = transform(v, transformation)
            bb_min[0] = min(bb_min[0], v[0])
            bb_min[1] = min(bb_min[1], v[1])
            bb_min[2] = min(bb_min[2], v[2])
            bb_max[0] = max(bb_max[0], v[0])
            bb_max[1] = max(bb_max[1], v[1])
            bb_max[2] = max(bb_max[2], v[2])

    for child in node.children:
        bb_min, bb_max = _compute_bounding_box_for_node(nodes, nodes[child], bb_min, bb_max, transformation)

    return bb_min, bb_max

def get_bounding_box_for_node(scene, node):
    bb_min = [1e10, 1e10, 1e10] # x,y,z
    bb_max = [-1e10, -1e10, -1e10] # x,y,z

    global_transformation = get_world_transform(scene, node)

    return _compute_bounding_box_for_node(scene.nodes, node, bb_min, bb_max, global_transformation)

def get_world_transform(scene, node):

    if node == scene.rootnode:
        return numpy.identity(4, dtype=numpy.float32)

    parents = reversed(_get_parent_chain(scene, node, []))
    parent_transform = reduce(numpy.dot, [p.transformation for p in parents])
    return numpy.dot(parent_transform, node.transformation)


def _get_parent_chain(scene, node, parents):

    parent = scene.nodes[node.parent]

    parents.append(parent)

    if parent == scene.rootnode:
        return parents

    return _get_parent_chain(scene, parent, parents)

def transformed_aabb(scene, node):
    """ TODO: this computation is incorrect! To compute a transformed AABB, we need to
    re-compute the AABB from the transformed *vertices* (or maybe from the transformed bounding box?)
    """
    parents = reversed(_get_parent_chain(scene, node, []))

    global_transformation = reduce(numpy.dot, [p.transformation for p in parents])
    
    return transform(node.aabb[0], global_transformation), \
           transform(node.aabb[1], global_transformation)
           
def compute_transformed_bounding_box(ctx, nodes, node, transformation, bb_min, bb_max):
    
    for mesh_id in node.properties["mesh_ids"]:
        mesh = ctx.mesh(mesh_id)
        for v in mesh.vertices:
            v = transform(v, transformation)
            bb_min[0] = float(round(min(bb_min[0], v[0]), 5))
            bb_min[1] = float(round(min(bb_min[1], v[1]), 5))
            bb_min[2] = float(round(min(bb_min[2], v[2]), 5))
            bb_max[0] = float(round(max(bb_max[0], v[0]), 5))
            bb_max[1] = float(round(max(bb_max[1], v[1]), 5))
            bb_max[2] = float(round(max(bb_max[2], v[2]), 5))
    
    for child in node.children:
        bb_min, bb_max = compute_transformed_bounding_box(nodes, nodes[child], transformation, bb_min, bb_max)
    
    return bb_min, bb_max
