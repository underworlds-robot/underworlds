#!/usr/bin/env python
#-*- coding: UTF-8 -*-

""" This program loads a underworlds world, and display its
3D scene.

Based on:
- pygame + mouselook code from http://3dengine.org/Spectator_%28PyOpenGL%29
 - http://www.lighthouse3d.com/tutorials
 - http://www.songho.ca/opengl/gl_transform.html
 - http://code.activestate.com/recipes/325391/
 - ASSIMP's C++ SimpleOpenGL viewer
"""
import sys
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import math
import numpy
from numpy import linalg

import logging; logger = logging.getLogger("underworlds.scene_viewer")
logging.basicConfig(level=logging.INFO)

import underworlds
from underworlds.types import *

def transform(vector3, matrix4x4):
    """ Apply a transformation matrix on a 3D vector.

    :param vector3: a numpy array with 3 elements
    :param matrix4x4: a numpy 4x4 matrix
    """
    return numpy.dot(matrix4x4, numpy.append(vector3, 1.))

def get_bounding_box(scene):
    nodes = scene.nodes
    bb_min = [1e10, 1e10, 1e10] # x,y,z
    bb_max = [-1e10, -1e10, -1e10] # x,y,z

    return get_bounding_box_for_node(nodes, scene.rootnode, bb_min, bb_max, linalg.inv(scene.rootnode.transformation))

def get_bounding_box_for_node(nodes, node, bb_min, bb_max, transformation):

    transformation = numpy.dot(transformation, node.transformation)
    if node.type == MESH:
        for v in node.aabb:
            v = transform(v, transformation)
            bb_min[0] = min(bb_min[0], v[0])
            bb_min[1] = min(bb_min[1], v[1])
            bb_min[2] = min(bb_min[2], v[2])
            bb_max[0] = max(bb_max[0], v[0])
            bb_max[1] = max(bb_max[1], v[1])
            bb_max[2] = max(bb_max[2], v[2])

    for child in node.children:
        bb_min, bb_max = get_bounding_box_for_node(nodes, nodes[child], bb_min, bb_max, transformation)

    return bb_min, bb_max

class Underworlds3DViewer:

    base_name = "Underworlds 3D viewer"

    def __init__(self, ctx, world, w=1024, h=768, fov=75):

        pygame.init()
        self.base_name = self.base_name + " <%s>" % world
        pygame.display.set_caption(self.base_name)
        pygame.display.set_mode((w,h), pygame.OPENGL | pygame.DOUBLEBUF)

        self.ctx = ctx
        self.world = ctx.worlds[world]

        self.scene = None
        self.meshes = {} # stores the OpenGL vertex/faces/normals buffers pointers
        self.cameras = []
        self.current_cam_index = 0

        self.load_world()

        # for FPS computation
        self.frames = 0
        self.last_fps_time = glutGet(GLUT_ELAPSED_TIME)


        glMatrixMode(GL_PROJECTION)
        aspect = w/h
        gluPerspective(fov, aspect, 0.001, 100000.0);
        glMatrixMode(GL_MODELVIEW)

    def prepare_gl_buffers(self, id):

        meshes = self.meshes

        if id in meshes:
            # mesh already loaded. Fine
            return

        meshes[id] = {}
        mesh = self.ctx.mesh(id) # retrieve the mesh from the server

        # Fill the buffer for vertex positions
        meshes[id]["vertices"] = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, meshes[id]["vertices"])
        glBufferData(GL_ARRAY_BUFFER, 
                    numpy.array(mesh["vertices"], dtype=numpy.float32),
                    GL_STATIC_DRAW)

        # Fill the buffer for normals
        meshes[id]["normals"] = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, meshes[id]["normals"])
        glBufferData(GL_ARRAY_BUFFER, 
                    numpy.array(mesh["normals"], dtype=numpy.float32),
                    GL_STATIC_DRAW)


        # Fill the buffer for vertex positions
        meshes[id]["faces"] = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, meshes[id]["faces"])
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, 
                    numpy.array(mesh["faces"], dtype=numpy.int32),
                    GL_STATIC_DRAW)

        meshes[id]["nbfaces"] = len(mesh["faces"])

        # Unbind buffers
        glBindBuffer(GL_ARRAY_BUFFER,0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,0)

    
    def load_world(self):
        logger.info("Preparing world <%s> for 3D rendering..." % self.world)

        scene = self.scene = self.world.scene
        nodes = scene.nodes
        for node in nodes:
            node.transformation = numpy.array(node.transformation)

        #log some statistics
        logger.info("  -> %d nodes" % len(nodes))
        self.bb_min, self.bb_max = get_bounding_box(scene)
        logger.info("  -> scene bounding box:" + str(self.bb_min) + " - " + str(self.bb_max))

        self.scene_center = [(a + b) / 2. for a, b in zip(self.bb_min, self.bb_max)]

        for node in nodes:
            if node.type == MESH:

                if hasattr(node, "cad"):
                    node.glmeshes = node.cad
                elif hasattr(node, "lowres"):
                    node.glmeshes = node.lowres
                elif hasattr(node, "hires"):
                    node.glmeshes = node.hires
                else:
                    raise StandardError("The node %s has no mesh available!" % node.name)

                for mesh in node.glmeshes:
                    self.prepare_gl_buffers(mesh)

            elif node.type == CAMERA:
                logger.info("Added camera <%s>" % node.name)
                self.cameras.append(node)
        logger.info("World <%s> ready for 3D rendering." % self.world)

    def simple_lights(self):
        glEnable(GL_LIGHTING)
        #glShadeModel(GL_SMOOTH)
        #glEnable(GL_LIGHT0)
        #glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.9, 0.45, 0.0, 1.0))
        #glLightfv(GL_LIGHT0, GL_POSITION, (0.0, 10.0, 10.0, 10.0))
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)

        glEnable(GL_CULL_FACE)

        glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)
        glEnable(GL_NORMALIZE)
        glEnable(GL_LIGHT0)

    def cycle_cameras(self):
        if not self.cameras:
            logger.info("No camera in the scene")
            return None
        self.current_cam_index = (self.current_cam_index + 1) % len(self.cameras)
        cam = self.cameras[self.current_cam_index]
        self.set_camera(cam)
        logger.info("Switched to camera " + str(cam))

    def set_camera(self, camera):

        znear = camera.clipplanenear
        zfar = camera.clipplanefar
        aspect = camera.aspect
        fov = camera.horizontalfov

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        # Compute gl frustrum
        tangent = math.tan(fov/2.)
        h = znear * tangent
        w = h * aspect

        # params: left, right, bottom, top, near, far
        glFrustum(-w, w, -h, h, znear, zfar)
        # equivalent to:
        #gluPerspective(fov * 180/math.pi, aspect, znear, zfar)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        cam = transform([0.0, 0.0, 0.0], camera.transformation)
        at = transform(camera.lookat, camera.transformation)
        gluLookAt(cam[0], cam[2], -cam[1],
                   at[0],  at[2],  -at[1],
                       0,      1,       0)

    def simple_camera_pose(self):
        """ Pre-position the camera (optional) """
        glMatrixMode(GL_MODELVIEW)
        glLoadMatrixf(numpy.array([0.741,-0.365,0.563,0,0,0.839,0.544,
            0,-0.671,-0.403,0.622,0,-0.649,1.72,-4.05,1]))

    def apply_material(self, mat):
        """ Apply an OpenGL, using one OpenGL list per material to cache 
        the operation.
        """

        if not hasattr(mat, "gl_mat"): # evaluate once the mat properties, and cache the values in a glDisplayList.
    
            diffuse = mat.properties.get("$clr.diffuse", numpy.array([0.8, 0.8, 0.8, 1.0]))
            specular = mat.properties.get("$clr.specular", numpy.array([0., 0., 0., 1.0]))
            ambient = mat.properties.get("$clr.ambient", numpy.array([0.2, 0.2, 0.2, 1.0]))
            emissive = mat.properties.get("$clr.emissive", numpy.array([0., 0., 0., 1.0]))
            shininess = min(mat.properties.get("$mat.shininess", 1.0), 128)
            wireframe = mat.properties.get("$mat.wireframe", 0)
            twosided = mat.properties.get("$mat.twosided", 1)
    
            from OpenGL.raw import GL
            setattr(mat, "gl_mat", GL.GLuint(0))
            mat.gl_mat = glGenLists(1)
            glNewList(mat.gl_mat, GL_COMPILE)
    
            glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, diffuse)
            glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, specular)
            glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, ambient)
            glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, emissive)
            glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, shininess)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if wireframe else GL_FILL)
            glDisable(GL_CULL_FACE) if twosided else glEnable(GL_CULL_FACE)
    
            glEndList()
    
        glCallList(mat.gl_mat)

    def recursive_render(self, node):
        """ Main recursive rendering method.
        """

        # save model matrix and apply node transformation
        glPushMatrix()
        m = node.transformation.transpose() # OpenGL row major
        glMultMatrixf(m)


        if node.type == MESH:
            for id in node.glmeshes:
                #self.apply_material(mesh.material)

                glBindBuffer(GL_ARRAY_BUFFER, self.meshes[id]["vertices"])
                glEnableClientState(GL_VERTEX_ARRAY)
                glVertexPointer(3, GL_FLOAT, 0, None)

                glBindBuffer(GL_ARRAY_BUFFER, self.meshes[id]["normals"])
                glEnableClientState(GL_NORMAL_ARRAY)
                glNormalPointer(GL_FLOAT, 0, None)

                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.meshes[id]["faces"])
                glDrawElements(GL_TRIANGLES, self.meshes[id]["nbfaces"] * 3, GL_UNSIGNED_INT, None)

                glDisableClientState(GL_VERTEX_ARRAY)
                glDisableClientState(GL_NORMAL_ARRAY)

                glBindBuffer(GL_ARRAY_BUFFER, 0)
                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

        for child in node.children:
            self.recursive_render(self.scene.nodes[child])

        glPopMatrix()


    def loop(self):
        pygame.display.flip()
        pygame.event.pump()
        self.keys = [k for k, pressed in enumerate(pygame.key.get_pressed()) if pressed]
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Compute FPS
        gl_time = glutGet(GLUT_ELAPSED_TIME)
        self.frames += 1
        if gl_time - self.last_fps_time >= 1000:
            current_fps = self.frames * 1000 / (gl_time - self.last_fps_time)
            pygame.display.set_caption(self.base_name + " - %.0f fps" % current_fps)
            self.frames = 0
            self.last_fps_time = gl_time


        return True

    def controls_3d(self,
                    mouse_button=1, \
                    up_key=pygame.K_UP, \
                    down_key=pygame.K_DOWN, \
                    left_key=pygame.K_LEFT, \
                    right_key=pygame.K_RIGHT):
        """ The actual camera setting cycle """
        mouse_dx,mouse_dy = pygame.mouse.get_rel()
        if pygame.mouse.get_pressed()[mouse_button]:
            look_speed = .2
            buffer = glGetDoublev(GL_MODELVIEW_MATRIX)
            c = (-1 * numpy.mat(buffer[:3,:3]) * \
                numpy.mat(buffer[3,:3]).T).reshape(3,1)
            # c is camera center in absolute coordinates, 
            # we need to move it back to (0,0,0) 
            # before rotating the camera
            glTranslate(c[0],c[1],c[2])
            m = buffer.flatten()
            glRotate(mouse_dx * look_speed, m[1],m[5],m[9])
            glRotate(mouse_dy * look_speed, m[0],m[4],m[8])
            
            # compensate roll
            glRotated(-math.atan2(-m[4],m[5]) * \
                57.295779513082320876798154814105 ,m[2],m[6],m[10])
            glTranslate(-c[0],-c[1],-c[2])

        # move forward-back or right-left
        if up_key in self.keys:
            fwd = .1
        elif down_key in self.keys:
            fwd = -.1
        else:
            fwd = 0

        if left_key in self.keys:
            strafe = .1
        elif right_key in self.keys:
            strafe = -.1
        else:
            strafe = 0

        if abs(fwd) or abs(strafe):
            m = glGetDoublev(GL_MODELVIEW_MATRIX).flatten()
            glTranslate(fwd*m[2],fwd*m[6],fwd*m[10])
            glTranslate(strafe*m[0],strafe*m[4],strafe*m[8])

if __name__ == '__main__':
    if not len(sys.argv) > 1:
        print("Usage: " + __file__ + " <world name>")
        sys.exit(2)

    with underworlds.Context("3D viewer") as ctx:
        app = Underworlds3DViewer(ctx, world = sys.argv[1])
        app.simple_lights()
        app.simple_camera_pose()

        while app.loop():
            app.recursive_render(app.scene.rootnode)
            app.controls_3d(0)
            if pygame.K_f in app.keys: pygame.display.toggle_fullscreen()
            if pygame.K_TAB in app.keys: app.cycle_cameras()
            if pygame.K_ESCAPE in app.keys: break
