#!/usr/bin/env python
#-*- coding: UTF-8 -*-

""" This program loads a underworlds world, and display its
3D scene.

Materials are supported but textures are currently ignored.

Half-working keyboard + mouse navigation is supported.

This sample is based on several sources, including:
 - http://www.lighthouse3d.com/tutorials
 - http://www.songho.ca/opengl/gl_transform.html
 - http://code.activestate.com/recipes/325391/
 - ASSIMP's C++ SimpleOpenGL viewer
"""

import os, sys
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *
from OpenGL.arrays import ArrayDatatype

import math
import numpy
from numpy import linalg

import logging; logger = logging.getLogger("underworlds.scene_viewer")
logging.basicConfig(level=logging.INFO)

import underworlds
from underworlds.types import *

name = 'Underworlds OpenGL viewer'
height = 600
width = 900

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





class GLRenderer():
    def __init__(self, ctx, world):

        self.ctx = ctx
        self.world = ctx.worlds[world]

        self.scene = None
        self.meshes = {} # stores the OpenGL vertex/faces/normals buffers pointers
        self.cameras = []

        self.drot = 0.0
        self.dp = 0.0

        self.angle = 0.0
        self.x = 1.0
        self.z = 3.0
        self.lx = 0.0
        self.lz = 0.0
        self.using_fixed_cam = False
        self.current_cam_index = 0

        self.x_origin = -1 # x position of the mouse when pressing left btn

        # for FPS calculation
        self.prev_time = 0
        self.prev_fps_time = 0
        self.frames = 0


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


    def cycle_cameras(self):
        if not self.cameras:
            logger.info("No camera in the scene")
            return None
        self.current_cam_index = (self.current_cam_index + 1) % len(self.cameras)
        cam = self.cameras[self.current_cam_index]
        logger.info("Switched to camera " + str(cam))
        return cam

    def set_default_camera(self):

        if not self.using_fixed_cam:
            glLoadIdentity()
            gluLookAt(self.x ,1., self.z, # pos
                    self.x + self.lx - 1.0, 1., self.z + self.lz - 3.0, # look at
                    0.,1.,0.) # up vector


    def set_camera(self, camera):

        if not camera:
            return

        self.using_fixed_cam = True

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

    def fit_scene(self, restore = False):
        """ Compute a scale factor and a translation to fit and center 
        the whole geometry on the screen.
        """

        x_max = self.bb_max[0] - self.bb_min[0]
        y_max = self.bb_max[1] - self.bb_min[1]
        tmp = max(x_max, y_max)
        z_max = self.bb_max[2] - self.bb_min[2]
        tmp = max(z_max, tmp)
        
        if not restore:
            tmp = 1. / tmp

        logger.info("Scaling the scene by %.03f" % tmp)
        glScalef(tmp, tmp, tmp)
    
        # center the model
        direction = -1 if not restore else 1
        glTranslatef( direction * self.scene_center[0], 
                      direction * self.scene_center[1], 
                      direction * self.scene_center[2] )

        return x_max, y_max, z_max
 
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

    
   
    def do_motion(self):

        gl_time = glutGet(GLUT_ELAPSED_TIME)

        # Compute the new position of the camera and set it
        self.x += self.dp * self.lx * 0.01 * (gl_time-self.prev_time)
        self.z += self.dp * self.lz * 0.01 * (gl_time-self.prev_time)
        self.angle += self.drot * 0.1 *  (gl_time-self.prev_time)
        self.lx = math.sin(self.angle)
        self.lz = -math.cos(self.angle)
        self.set_default_camera()

        self.prev_time = gl_time

        # Compute FPS
        self.frames += 1
        if gl_time - self.prev_fps_time >= 1000:
            current_fps = self.frames * 1000 / (gl_time - self.prev_fps_time)
            logger.info('%.0f fps' % current_fps)
            self.frames = 0
            self.prev_fps_time = gl_time

        glutPostRedisplay()

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


    def display(self):
        """ GLUT callback to redraw OpenGL surface
        """
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

        #glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        #glEnable(GL_CULL_FACE)

        self.recursive_render(self.scene.rootnode)
    
        glutSwapBuffers()
        self.do_motion()
        return

    ####################################################################
    ##               GLUT keyboard and mouse callbacks                ##
    ####################################################################
    def onkeypress(self, key, x, y):
        if key == 'c':
            self.fit_scene(restore = True)
            self.set_camera(self.cycle_cameras())
        if key == 'q':
            glutLeaveMainLoop()

    def onspecialkeypress(self, key, x, y):

        fraction = 0.05

        if key == GLUT_KEY_UP:
            self.dp = 0.5
        if key == GLUT_KEY_DOWN:
            self.dp = -0.5
        if key == GLUT_KEY_LEFT:
            self.drot = -0.01
        if key == GLUT_KEY_RIGHT:
            self.drot = 0.01

    def onspecialkeyrelease(self, key, x, y):

        if key == GLUT_KEY_UP:
            self.dp = 0.
        if key == GLUT_KEY_DOWN:
            self.dp = 0.
        if key == GLUT_KEY_LEFT:
            self.drot = 0.0
        if key == GLUT_KEY_RIGHT:
            self.drot = 0.0

    def onclick(self, button, state, x, y):
        if button == GLUT_LEFT_BUTTON:
            if state == GLUT_UP:
                self.drot = 0
                self.x_origin = -1
            else: # GLUT_DOWN
                self.x_origin = x

    def onmousemove(self, x, y):
        if self.x_origin >= 0:
            self.drot = (x - self.x_origin) * 0.001

    def render(self, fullscreen = False, autofit = True, postprocess = None):
        """

        :param autofit: if true, scale the scene to fit the whole geometry
        in the viewport.
        """
    
        # First initialize the openGL context
        glutInit(sys.argv)
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
        if not fullscreen:
            glutInitWindowSize(width, height)
            glutCreateWindow(name)
        else:
            glutGameModeString("1024x768")
            if glutGameModeGet(GLUT_GAME_MODE_POSSIBLE):
                glutEnterGameMode()
            else:
                print("Fullscreen mode not available!")
                sys.exit(1)


        self.load_world()

        glClearColor(0.1,0.1,0.1,1.)
        #glShadeModel(GL_SMOOTH)

        glEnable(GL_LIGHTING)

        glEnable(GL_CULL_FACE)
        glEnable(GL_DEPTH_TEST)

        #lightZeroPosition = [10.,4.,10.,1.]
        #lightZeroColor = [0.8,1.0,0.8,1.0] #green tinged
        #glLightfv(GL_LIGHT0, GL_POSITION, lightZeroPosition)
        #glLightfv(GL_LIGHT0, GL_DIFFUSE, lightZeroColor)
        #glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION, 0.1)
        #glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.05)
        glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)
        glEnable(GL_NORMALIZE)
        glEnable(GL_LIGHT0)
    
        glutDisplayFunc(self.display)


        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(35.0, width/float(height) , 0.10, 100.0)
        glMatrixMode(GL_MODELVIEW)
        self.set_default_camera()

        if autofit:
            # scale the whole asset to fit into our view frustum·
            self.fit_scene()

        glPushMatrix()

        # Register GLUT callbacks for keyboard and mouse
        glutKeyboardFunc(self.onkeypress)
        glutSpecialFunc(self.onspecialkeypress)
        glutIgnoreKeyRepeat(1)
        glutSpecialUpFunc(self.onspecialkeyrelease)

        glutMouseFunc(self.onclick)
        glutMotionFunc(self.onmousemove)

        glutMainLoop()


if __name__ == '__main__':
    if not len(sys.argv) > 1:
        print("Usage: " + __file__ + " <world name>")
        sys.exit(2)

    world = sys.argv[1]

    with underworlds.Context("3D viewer") as ctx:
        glrender = GLRenderer(ctx, world)
        glrender.render(fullscreen = False)

