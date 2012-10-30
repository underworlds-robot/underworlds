#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import os, sys
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *
from OpenGL.arrays import ArrayDatatype

import logging;logger = logging.getLogger("assimp_opengl")
logging.basicConfig(level=logging.INFO)

import math
import numpy

from pyassimp import core as pyassimp
from pyassimp.postprocess import *
from pyassimp.helper import *


name = 'pyassimp OpenGL viewer'
height = 600
width = 900

SAMPLES_LIMIT_FOR_VISIBILITY = 100 # below this value, a mesh is not considered as visible. Be careful! The check is resolution dependent!

class GLRenderer():
    def __init__(self, filename=None, postprocess = None):

        self.filename = filename
        self.postprocess = postprocess

        self.scene = None

        self.current_cam_index = 0

        # for FPS calculation
        self.prev_time = 0
        self.prev_fps_time = 0
        self.frames = 0

        self.visibilities = {}

    def prepare_gl_buffers(self, mesh):

        mesh.gl = {}

        # Fill the buffer for vertex positions
        mesh.gl["vertices"] = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, mesh.gl["vertices"])
        glBufferData(GL_ARRAY_BUFFER, 
                    mesh.vertices,
                    GL_STATIC_DRAW)

        # Fill the buffer for normals
        mesh.gl["normals"] = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, mesh.gl["normals"])
        glBufferData(GL_ARRAY_BUFFER, 
                    mesh.normals,
                    GL_STATIC_DRAW)


        # Fill the buffer for vertex positions
        mesh.gl["triangles"] = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, mesh.gl["triangles"])
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, 
                    mesh.faces,
                    GL_STATIC_DRAW)

        # Unbind buffers
        glBindBuffer(GL_ARRAY_BUFFER,0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,0)

    
    def load_dae(self, path, postprocess = None):
        logger.info("Loading model:" + path + "...")

        if postprocess:
            self.scene = pyassimp.load(path, postprocess)
        else:
            self.scene = pyassimp.load(path)
        logger.info("Done.")

        scene = self.scene
        #log some statistics
        logger.info("  meshes: %d" % len(scene.meshes))
        logger.info("  total faces: %d" % sum([len(mesh.faces) for mesh in scene.meshes]))
        logger.info("  materials: %d" % len(scene.materials))
        self.bb_min, self.bb_max = get_bounding_box(self.scene)
        logger.info("  bounding box:" + str(self.bb_min) + " - " + str(self.bb_max))

        self.scene_center = [(a + b) / 2. for a, b in zip(self.bb_min, self.bb_max)]

        for index, mesh in enumerate(scene.meshes):
            self.prepare_gl_buffers(mesh)

        # Finally release the model
        pyassimp.release(scene)

    def cycle_cameras(self):
        self.current_cam_index
        if not self.scene.cameras:
            return None
        self.current_cam_index = (self.current_cam_index + 1) % len(self.scene.cameras)
        cam = self.scene.cameras[self.current_cam_index]
        logger.info("Switched to camera " + str(cam))
        self.set_camera(cam)

    def get_visibilities(self):

        self.init_gl()

        glPolygonMode(GL_FRONT_AND_BACK, GL_POINT) # no need to fill the faces
        start_time = glutGet(GLUT_ELAPSED_TIME)

        for cam in self.scene.cameras:
            self.set_camera(cam)

            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
            self.recursive_render(self.scene.rootnode)

        end_time = glutGet(GLUT_ELAPSED_TIME)
        print("Computed visibilities in " + str(end_time - start_time) + "ms.\n" + str(self.visibilities))

    def set_visibility(self, node, samples):

        state = True if samples > 100 else False

        self.visibilities.setdefault(self.current_cam, {})[node] = state


    def set_camera(self, camera):

        self.current_cam = camera.name
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

        cam = transform(camera.position, camera.transformation)
        at = transform(camera.lookat, camera.transformation)
        gluLookAt(cam[0], cam[2], -cam[1],
                   at[0],  at[2],  -at[1],
                       0,      1,       0)

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
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if wireframe else GL_FILL) # no need to fill the faces
            glDisable(GL_CULL_FACE) if twosided else glEnable(GL_CULL_FACE)
    
            glEndList()
    
        glCallList(mat.gl_mat)

    
   
    def do_motion(self):

        gl_time = glutGet(GLUT_ELAPSED_TIME)

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

        if node.meshes:
            if not hasattr(node, "occulsion_query"):
                node.occlusion_query = glGenQueries(1)
            glBeginQuery(GL_SAMPLES_PASSED, node.occlusion_query)

            for mesh in node.meshes:
                self.apply_material(mesh.material)

                glBindBuffer(GL_ARRAY_BUFFER, mesh.gl["vertices"])
                glEnableClientState(GL_VERTEX_ARRAY)
                glVertexPointer(3, GL_FLOAT, 0, None)

                glBindBuffer(GL_ARRAY_BUFFER, mesh.gl["normals"])
                glEnableClientState(GL_NORMAL_ARRAY)
                glNormalPointer(GL_FLOAT, 0, None)

                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, mesh.gl["triangles"])
                glDrawElements(GL_TRIANGLES,len(mesh.faces) * 3, GL_UNSIGNED_INT, None)

                glDisableClientState(GL_VERTEX_ARRAY)
                glDisableClientState(GL_NORMAL_ARRAY)

                glBindBuffer(GL_ARRAY_BUFFER, 0)
                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)


            glEndQuery(GL_SAMPLES_PASSED)
            samples = glGetQueryObjectuiv(node.occlusion_query, GL_QUERY_RESULT)
            self.set_visibility(node.name, samples)

        for child in node.children:
            self.recursive_render(child)

        glPopMatrix()

            

    def display(self):
        """ GLUT callback to redraw OpenGL surface
        """
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    
        self.recursive_render(self.scene.rootnode)
    
        glutSwapBuffers()
        self.do_motion()
        return

    def onkeypress(self, key, x, y):
        if key == 'c':
            self.cycle_cameras()
        if key == 'q':
            sys.exit(0)

   
    def init_gl(self):
        # First initialize the openGL context
        glutInit(sys.argv)
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
        glutInitWindowSize(width, height)
        glutCreateWindow(name)

        self.load_dae(self.filename, postprocess = self.postprocess)

        glEnable(GL_CULL_FACE)
        glEnable(GL_DEPTH_TEST)



    def render(self):
        """

        :param autofit: if true, scale the scene to fit the whole geometry
        in the viewport.
        """
 
        self.init_gl()

        # init lighting
        glClearColor(0.,0.,0.,1.)

        glEnable(GL_LIGHTING)

        glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)
        glEnable(GL_NORMALIZE)
        glEnable(GL_LIGHT0)

        glutDisplayFunc(self.display)


        self.cycle_cameras()

        glPushMatrix()

        glutKeyboardFunc(self.onkeypress)

        glutMainLoop()


if __name__ == '__main__':
    if not len(sys.argv) > 1:
        print("Usage: " + __file__ + " <model>")
        sys.exit(0)

    glrender = GLRenderer(sys.argv[1], postprocess = aiProcessPreset_TargetRealtime_MaxQuality)
    #glrender.get_visibilities()
    glrender.render()

