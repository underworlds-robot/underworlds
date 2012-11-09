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

import logging
logger = logging.getLogger("underworlds.3d_viewer")
gllogger = logging.getLogger("OpenGL")
gllogger.setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO)

import OpenGL
#OpenGL.ERROR_CHECKING=False
#OpenGL.ERROR_LOGGING = False
#OpenGL.ERROR_ON_COPY = True
#OpenGL.FULL_LOGGING = True
from OpenGL.GL import *
from OpenGL.error import GLError
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.arrays import vbo
from OpenGL.GL import shaders
from OpenGL.GL.framebufferobjects import *

import pygame

import math
import numpy
from numpy import linalg


import underworlds
from underworlds.types import *

from fontmanager import FontManager

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

class DefaultCamera:
    def __init__(self, w, h, fov):
        self.clipplanenear = 0.001
        self.clipplanefar = 100000.0
        self.aspect = w/h
        self.horizontalfov = fov * math.pi/180
        self.transformation = [[ 0.68, -0.32, 0.65, 7.48],
                               [ 0.73,  0.31, -0.61, -6.51],
                               [-0.01,  0.89,  0.44,  5.34],
                               [ 0.,    0.,    0.,    1.  ]]
        self.lookat = [0.0,0.0,-1.0]

    def __str__(self):
        return "Default camera"


class Underworlds3DViewer:

    base_name = "Underworlds 3D viewer"

    def __init__(self, ctx, world, w=1024, h=768, fov=75):

        self.w = w
        self.h = h

        pygame.init()
        self.base_name = self.base_name + " <%s>" % world
        pygame.display.set_caption(self.base_name)
        pygame.display.set_mode((w,h), pygame.OPENGL | pygame.DOUBLEBUF)

        self.prepare_shaders()

        self.fontmanager = FontManager("aller.ttf", w, h, 18)

        self.ctx = ctx
        self.world = ctx.worlds[world]

        self.scene = None
        self.meshes = {} # stores the OpenGL vertex/faces/normals buffers pointers
        self.cameras = [DefaultCamera(w,h,fov)]
        self.current_cam_index = 0

        self.load_world()

        # for FPS computation
        self.frames = 0
        self.last_fps_time = glutGet(GLUT_ELAPSED_TIME)


        self.cycle_cameras()

    def prepare_shaders(self):

        phong_weightCalc = """
        float phong_weightCalc(
            in vec3 light_pos, // light position
            in vec3 frag_normal // geometry normal
        ) {
            // returns vec2( ambientMult, diffuseMult )
            float n_dot_pos = max( 0.0, dot(
                frag_normal, light_pos
            ));
            return n_dot_pos;
        }
        """

        flatvertex = shaders.compileShader(
        """
        uniform vec4 Material_diffuse;
        attribute vec3 Vertex_position;
        varying vec4 baseColor;
        void main() {
            gl_Position = gl_ModelViewProjectionMatrix * vec4(
                Vertex_position, 1.0
            );
            baseColor = Material_diffuse;
        }""", GL_VERTEX_SHADER)

        vertex = shaders.compileShader( phong_weightCalc +
        """
        uniform vec4 Global_ambient;
        uniform vec4 Light_ambient;
        uniform vec4 Light_diffuse;
        uniform vec3 Light_location;
        uniform vec4 Material_ambient;
        uniform vec4 Material_diffuse;
        attribute vec3 Vertex_position;
        attribute vec3 Vertex_normal;
        varying vec4 baseColor;
        void main() {
            gl_Position = gl_ModelViewProjectionMatrix * vec4(
                Vertex_position, 1.0
            );
            vec3 EC_Light_location = gl_NormalMatrix * Light_location;
            float diffuse_weight = phong_weightCalc(
                normalize(EC_Light_location),
                normalize(gl_NormalMatrix * Vertex_normal)
            );
            baseColor = clamp(
            (
                // global component
                (Global_ambient * Material_ambient)
                // material's interaction with light's contribution
                // to the ambient lighting...
                + (Light_ambient * Material_ambient)
                // material's interaction with the direct light from
                // the light.
                + (Light_diffuse * Material_diffuse * diffuse_weight)
            ), 0.0, 1.0);
        }""", GL_VERTEX_SHADER)

        fragment = shaders.compileShader("""
        varying vec4 baseColor;
        void main() {
            gl_FragColor = baseColor;
        }
        """, GL_FRAGMENT_SHADER)

        self.flatshader = shaders.compileProgram(flatvertex,fragment)
        self.set_shader_accessors( ('Material_diffuse',), ('Vertex_position',), self.flatshader)

        self.shader = shaders.compileProgram(vertex,fragment)
        self.set_shader_accessors( (
            'Global_ambient',
            'Light_ambient','Light_diffuse','Light_location',
            'Material_ambient','Material_diffuse',
        ), (
            'Vertex_position','Vertex_normal',
        ), self.shader)

    def set_shader_accessors(self, uniforms, attributes, shader):
        # add accessors to the shaders uniforms and attributes
        for uniform in uniforms:
            location = glGetUniformLocation( shader,  uniform )
            if location in (None,-1):
                logger.warning('No uniform: %s'%( uniform ))
            setattr( shader, uniform, location )

        for attribute in attributes:
            location = glGetAttribLocation( shader, attribute )
            if location in (None,-1):
                logger.warning('No attribute: %s'%( attribute ))
            setattr( shader, attribute, location )

    def prepare_gl_buffers(self, id):

        meshes = self.meshes

        if id in meshes:
            # mesh already loaded. Fine
            return

        meshes[id] = {}

        # leave some time for new nodes to push their meshes
        while not self.ctx.has_mesh(id):
            time.sleep(0.01)

        mesh = self.ctx.mesh(id) # retrieve the mesh from the server

        # Fill the buffer for vertex and normals positions
        v = numpy.array(mesh["vertices"], 'f')
        n = numpy.array(mesh["normals"], 'f')

        #meshes[id]["vbo"] = glGenBuffers(1)
        #glBindBuffer(GL_ARRAY_BUFFER, meshes[id]["vbo"])
        #glBufferData(GL_ARRAY_BUFFER, 
        #            numpy.hstack((v,n)), # concatenate vertices and normals in one array
        #            GL_STATIC_DRAW)

        meshes[id]["vbo"] = vbo.VBO(numpy.hstack((v,n)))

        # Fill the buffer for vertex positions
        meshes[id]["faces"] = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, meshes[id]["faces"])
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, 
                    numpy.array(mesh["faces"], dtype=numpy.int32),
                    GL_STATIC_DRAW)

        meshes[id]["nbfaces"] = len(mesh["faces"])
        meshes[id]["material"] = mesh["material"]

        # Unbind buffers
        glBindBuffer(GL_ARRAY_BUFFER,0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,0)

    def glize(self, node):

        logger.info("Loading node <%s>" % node)

        node.transformation = numpy.array(node.transformation)

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


    def load_world(self):
        logger.info("Preparing world <%s> for 3D rendering..." % self.world)

        scene = self.scene = self.world.scene
        nodes = scene.nodes
        for node in nodes:
            self.glize(node)

        #log some statistics
        logger.info("  -> %d nodes" % len(nodes))
        self.bb_min, self.bb_max = get_bounding_box(scene)
        logger.info("  -> scene bounding box:" + str(self.bb_min) + " - " + str(self.bb_max))

        self.scene_center = [(a + b) / 2. for a, b in zip(self.bb_min, self.bb_max)]

        logger.info("World <%s> ready for 3D rendering." % self.world)

    def cycle_cameras(self):
        if not self.cameras:
            logger.info("No camera in the scene")
            return None
        self.current_cam_index = (self.current_cam_index + 1) % len(self.cameras)
        self.current_cam = self.cameras[self.current_cam_index]
        self.set_camera(self.current_cam)
        logger.info("Switched to camera <%s>" % self.current_cam)

    def set_overlay_projection(self):
        glViewport(0,0,self.w,self.h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0.0, self.w - 1.0, 0.0, self.h - 1.0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def set_camera_projection(self, camera = None):

        if not camera:
            camera = self.cameras[self.current_cam_index]

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


    def set_camera(self, camera):

        self.set_camera_projection(camera)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        cam = transform([0.0, 0.0, 0.0], camera.transformation)
        at = transform(camera.lookat, camera.transformation)
        gluLookAt(cam[0], cam[2], -cam[1],
                   at[0],  at[2],  -at[1],
                       0,      1,       0)

    def render_colors(self):

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)


        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glEnable(GL_CULL_FACE)

        glUseProgram(self.flatshader)

        self.recursive_render(self.scene.rootnode, self.flatshader, normals = False, ambient = False)

        glUseProgram( 0 )

    def render(self, wireframe = False, twosided = False):

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)


        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if wireframe else GL_FILL)
        glDisable(GL_CULL_FACE) if twosided else glEnable(GL_CULL_FACE)

        shader = self.shader

        glUseProgram(shader)
        glUniform4f( shader.Global_ambient, .4,.2,.2,.1 )
        glUniform4f( shader.Light_ambient, .4,.4,.4, 1.0 )
        glUniform4f( shader.Light_diffuse, 1,1,1,1 )
        glUniform3f( shader.Light_location, 2,2,10 )

        self.recursive_render(self.scene.rootnode, shader)

        glUseProgram( 0 )

    def recursive_render(self, node, shader, normals = True, ambient = True):
        """ Main recursive rendering method.
        """

        # save model matrix and apply node transformation
        glPushMatrix()
        try:
            m = node.transformation.transpose() # OpenGL row major
        except AttributeError:
            #probably a new incoming node, that has not yet been converted to numpy
            self.glize(node)
            m = node.transformation.transpose() # OpenGL row major
        glMultMatrixf(m)

        if node.type == MESH:


            for id in node.glmeshes:

                stride = 24 # 6 * 4 bytes

                mat = self.meshes[id]["material"]
                glUniform4f( shader.Material_diffuse, *mat["diffuse"] )
                if ambient:
                    glUniform4f( shader.Material_ambient, *mat["ambient"] )


                vbo = self.meshes[id]["vbo"]
                vbo.bind()

                glEnableVertexAttribArray( shader.Vertex_position )
                if normals:
                    glEnableVertexAttribArray( shader.Vertex_normal )

                glVertexAttribPointer(
                    shader.Vertex_position,
                    3, GL_FLOAT,False, stride, vbo
                )

                if normals:
                    glVertexAttribPointer(
                        shader.Vertex_normal,
                        3, GL_FLOAT,False, stride, vbo+12
                    )

                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.meshes[id]["faces"])
                glDrawElements(GL_TRIANGLES, self.meshes[id]["nbfaces"] * 3, GL_UNSIGNED_INT, None)


                vbo.unbind()
                glDisableVertexAttribArray( shader.Vertex_position )

                if normals:
                    glDisableVertexAttribArray( shader.Vertex_normal )


                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

        for child in node.children:
            self.recursive_render(self.scene.nodes[child], shader, normals, ambient)

        glPopMatrix()

    def switch_to_overlay(self):
        glPushMatrix()
        self.set_overlay_projection()

    def switch_from_overlay(self):
        self.set_camera_projection()
        glPopMatrix()


    def display(self, text, x, y):
        self.fontmanager.display(text,x,y)

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

        while app.loop():
            #app.render()
            app.render_colors()
            app.switch_to_overlay()
            app.display("world <%s>"% app.world, 10,10)
            app.switch_from_overlay()
            app.controls_3d(0)
            if pygame.K_f in app.keys: pygame.display.toggle_fullscreen()
            if pygame.K_TAB in app.keys: app.cycle_cameras()
            if pygame.K_ESCAPE in app.keys: break
