import OpenGL
#OpenGL.ERROR_CHECKING=False
#OpenGL.ERROR_LOGGING = False
#OpenGL.ERROR_ON_COPY = True
#OpenGL.FULL_LOGGING = True
from OpenGL.GL import *
from OpenGL.error import GLError
from OpenGL.GLU import *
from OpenGL.arrays import vbo
from OpenGL.GL import shaders

import math, random
import numpy
from numpy import linalg

import logging
logger = logging.getLogger("underworlds.visibility")

import underworlds
from underworlds.types import *
from underworlds.helpers.geometry import transform, get_world_transform
from underworlds.helpers import transformations


FLAT_VERTEX_SHADER="""
#version 130

uniform mat4 u_viewProjectionMatrix;
uniform mat4 u_modelMatrix;

uniform vec4 u_materialDiffuse;

in vec3 a_vertex;

out vec4 v_color;

void main(void)
{
    v_color = u_materialDiffuse;
    gl_Position = u_viewProjectionMatrix * u_modelMatrix * vec4(a_vertex, 1.0);
}
"""

BASIC_FRAGMENT_SHADER="""
#version 130

in vec4 v_color;

void main() {
    gl_FragColor = v_color;
}
"""


class VisibilityMonitor:


    def __init__(self, ctx, world, w=80, h=60, create_surface=True):

        self.w = w
        self.h = h

        if create_surface:
            import pygame
            pygame.init()
            pygame.display.set_mode((w,h), pygame.OPENGL | pygame.DOUBLEBUF)
            pygame.display.iconify()

        self.prepare_shaders()

        self.ctx = ctx
        self.world = world

        self.scene = None
        self.meshes = {} # stores the OpenGL vertex/faces/normals buffers pointers

        self.node2colorid = {} # stores a color ID for each node. Useful for mouse picking and visibility checking
        self.colorid2node = {} # reverse dict of node2colorid

        self.currently_selected = None

        self.cameras = []
        self.current_cam_index = 0

        self.load_world()

        if not self.cameras:
            raise RuntimeError("No camera in the world <%s>. Giving up." % self.world)

    def prepare_shaders(self):

        ### Flat shader
        flatvertex = shaders.compileShader(FLAT_VERTEX_SHADER, GL_VERTEX_SHADER)
        fragment = shaders.compileShader(BASIC_FRAGMENT_SHADER, GL_FRAGMENT_SHADER)

        self.flatshader = shaders.compileProgram(flatvertex,fragment)

        self.set_shader_accessors( ('u_modelMatrix',
                                    'u_viewProjectionMatrix',
                                    'u_materialDiffuse',), 
                                    ('a_vertex',), self.flatshader)


    def set_shader_accessors(self, uniforms, attributes, shader):
        # add accessors to the shaders uniforms and attributes
        for uniform in uniforms:
            location = glGetUniformLocation( shader,  uniform )
            if location in (None,-1):
                raise RuntimeError('No uniform: %s (maybe it is not used '
                                   'anymore and has been optimized out by'
                                   ' the shader compiler)'%( uniform ))
            setattr( shader, uniform, location )

        for attribute in attributes:
            location = glGetAttribLocation( shader, attribute )
            if location in (None,-1):
                raise RuntimeError('No attribute: %s'%( attribute ))
            setattr( shader, attribute, location )

    def prepare_gl_buffers(self, id):

        meshes = self.meshes

        if id in meshes:
            # mesh already loaded. Fine
            return

        meshes[id] = {}

        # leave some time for new nodes to push their meshes
        if not self.ctx.has_mesh(id):
            logger.warning("Mesh ID %s is not available on the server... "
                           "waiting for it..." % id)
            while not self.ctx.has_mesh(id):
                time.sleep(0.01)

            logger.info("Mesh ID %s is now available. Getting it..." % id)

        mesh = self.ctx.mesh(id) # retrieve the mesh from the server

        # Fill the buffer for vertex
        v = numpy.array(mesh.vertices, 'f')

        meshes[id]["vbo"] = vbo.VBO(v)

        # Fill the buffer with faces indices
        meshes[id]["faces"] = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, meshes[id]["faces"])
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, 
                    numpy.array(mesh.faces, dtype=numpy.int32),
                    GL_STATIC_DRAW)

        meshes[id]["nbfaces"] = len(mesh.faces)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,0)

    def get_rgb_from_colorid(self, colorid):
        r = (colorid >> 0) & 0xff
        g = (colorid >> 8) & 0xff
        b = (colorid >> 16) & 0xff

        return (r,g,b)

    def get_color_id(self):
        id = random.randint(0, 256*256*256)
        if id not in self.colorid2node:
            return id
        else:
            return self.get_color_id()

    def glize(self, node):


        if node.type == MESH:
            colorid = self.get_color_id()
            self.colorid2node[colorid] = node
            self.node2colorid[node] = colorid

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
            logger.info("Loading node <%s>" % node)
            self.glize(node)

        logger.info("World <%s> ready for visibility monitoring." % self.world)

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

        self.projection_matrix = glGetFloatv( GL_PROJECTION_MATRIX).transpose()

        self.view_matrix = linalg.inv(camera.transformation)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glMultMatrixf(self.view_matrix.transpose())


    def render_colors(self):

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)

        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glEnable(GL_CULL_FACE)

        glUseProgram(self.flatshader)

        glUniformMatrix4fv( self.flatshader.u_viewProjectionMatrix, 1, GL_TRUE,
                            numpy.dot(self.projection_matrix,self.view_matrix))


        self.recursive_render(self.scene.rootnode, self.flatshader)

        glUseProgram( 0 )

    def compute(self):
        """
        :returns: dictionary {camera: [visible nodes]}
        Attention: The performances of this method relies heavily on the size of the display!
        """
        visible_objects = {}

        for c in self.cameras:
                
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.set_camera(c)
            self.render_colors()
            # Capture image from the OpenGL buffer
            buf = ( GLubyte * (3 * self.w * self.h) )(0)
            glReadPixels(0, 0, self.w, self.h, GL_RGB, GL_UNSIGNED_BYTE, buf)

            #Reinterpret the RGB pixel buffer as a 1-D array of 24bits colors
            a = numpy.ndarray(len(buf), numpy.dtype('>u1'), buf)
            colors = numpy.zeros(len(buf) / 3, numpy.dtype('<u4'))
            for i in range(3):
                colors.view(dtype='>u1')[i::4] = a.view(dtype='>u1')[i::3]

            seen = numpy.unique(colors)
            seen.sort()
            seen = seen[1:] # remove the 0 for background

            visible_objects[c] = [self.colorid2node[i] for i in seen]

            #colors = colors[numpy.nonzero(colors)] #discard black background
            
            #if colors.any():
            #    bins = numpy.bincount(colors)
            #    ii = numpy.nonzero(bins)[0]

            #    for i in ii:
            #        print ("Node %s is visible (%d pix)" % (self.colorid2node[i], bins[i]))
            #else:
            #    print("Nothing visible!")

        return visible_objects

    def recursive_render(self, node, shader):
        """ Main recursive rendering method.
        """

        try:
            m = get_world_transform(self.scene, node)
        except AttributeError:
            #probably a new incoming node, that has not yet been converted to numpy
            self.glize(node)
            m = get_world_transform(self.scene, node)

        if node.type == MESH:

            # if the node has been recently turned into a mesh, we might not
            # have the mesh data yet.
            if not hasattr(node, "glmeshes"):
                self.glize(node)

            for id in node.glmeshes:

                stride = 12 # 3 * 4 bytes

                colorid = self.node2colorid[node]
                r,g,b= self.get_rgb_from_colorid(colorid)
                glUniform4f( shader.u_materialDiffuse, r/255.0,g/255.0,b/255.0,1.0 )

                glUniformMatrix4fv( shader.u_modelMatrix, 1, GL_TRUE, m )

                vbo = self.meshes[id]["vbo"]
                vbo.bind()

                glEnableVertexAttribArray( shader.a_vertex )

                glVertexAttribPointer(
                    shader.a_vertex,
                    3, GL_FLOAT,False, stride, vbo
                )

                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.meshes[id]["faces"])
                glDrawElements(GL_TRIANGLES, self.meshes[id]["nbfaces"] * 3, GL_UNSIGNED_INT, None)


                vbo.unbind()
                glDisableVertexAttribArray( shader.a_vertex )

                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

        for child in node.children:
            try:
                self.recursive_render(self.scene.nodes[child], shader)
            except KeyError as ke:
                logger.warning("Node ID %s listed as child of %s, but it"
                                " does not exist! Skipping it" % (child, repr(node)))



