## {{{ http://code.activestate.com/recipes/325391/ (r1)
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *
from OpenGL.GL.ARB.vertex_buffer_object import *
from OpenGL.arrays import ArrayDatatype

from pyassimp import pyassimp
import os, sys

from assimp_postprocess import *

import numpy

name = 'ball_glut'
#get a model out of assimp's test-data if none is provided on the command line
DEFAULT_MODEL = "test.dae"

vertexLoc = 0
normalLoc = 1
texCoordLoc = 2

meshes = []

def load_transformation(assimp_matrix):
     assimp_matrix.Transpose() # OpenGL row major
     matrix = (GLfloat * len(assimp_matrix))(*assimp_matrix)
     glTranslatef(self.x, self.y, self.z)
     glMultMatrixf(matrix)

def prepare_gl_buffers(mesh):

        gl_mesh = {}

        print "  MESH:"
        print "    material:", mesh.mMaterialIndex+1
        print "    vertices:", len(mesh.vertices)
        print "    first 3 verts:", mesh.vertices[:3]
        if len(mesh.normals):
                print "    first 3 normals:", mesh.normals[:3]
        print "    colors:", len(mesh.colors)
        print "    faces:", len(mesh.faces), "first:", [f.indices for f in mesh.faces[:3]]
        print "    bones:", len(mesh.bones), "first:", [b.mName for b in mesh.bones[:3]]
        print
        
        gl_mesh["nb_faces"] = len(mesh.faces)
        
        triangles = []
        for face in mesh.faces:
            for i in face.indices:
                triangles += [i]

        triangles = numpy.array(triangles)
        vertices = numpy.array([[v[0],v[1],v[2]] for v in mesh.vertices], "f")
        normals = numpy.array([[v[0],v[1],v[2]] for v in mesh.normals], "f")
       
       # Fill the buffer for vertex positions
        gl_mesh["vertices"] = glGenBuffersARB(1)
        glBindBufferARB(GL_ARRAY_BUFFER_ARB, gl_mesh["vertices"])
        glBufferDataARB(GL_ARRAY_BUFFER_ARB, 
                    ArrayDatatype.arrayByteCount(vertices),
                    ArrayDatatype.voidDataPointer(vertices),
                    GL_STATIC_DRAW_ARB)
       # Fill the buffer for normals
        gl_mesh["normals"] = glGenBuffersARB(1)
        glBindBufferARB(GL_ARRAY_BUFFER_ARB, gl_mesh["normals"])
        glBufferDataARB(GL_ARRAY_BUFFER_ARB, 
                    ArrayDatatype.arrayByteCount(normals),
                    ArrayDatatype.voidDataPointer(normals),
                    GL_STATIC_DRAW_ARB)


        # Fill the buffer for vertex positions
        gl_mesh["triangles"] = glGenBuffersARB(1)
        glBindBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB, gl_mesh["triangles"])
        glBufferDataARB(GL_ELEMENT_ARRAY_BUFFER_ARB, 
                    ArrayDatatype.arrayByteCount(triangles),
                    ArrayDatatype.voidDataPointer(triangles),
                    GL_STATIC_DRAW_ARB)
        gl_mesh["triangles_data"] = triangles

        # Unbind buffers
        glBindBufferARB(GL_ARRAY_BUFFER_ARB,0)
        glBindBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB,0)

        return gl_mesh

def load_dae(path):
    #scene = pyassimp.load(path, aiProcessPreset_TargetRealtime_Quality)
    scene = pyassimp.load(path)

    tree_exploration(scene.rootnode)
    #the model we load
    print "MODEL:", path
    print
    
    #write some statistics
    print "SCENE:"
    print "  meshes:", len(scene.meshes)
    print "  materials:", len(scene.materials)
    print "  textures:", len(scene.textures)
    print
    
    print "MESHES:"

    for index, mesh in enumerate(scene.meshes):
        gl_mesh = prepare_gl_buffers(mesh)
        import pdb;pdb.set_trace()
        gl_mesh["transformation"] = "toto"
        meshes.append(gl_mesh)

    print "MATERIALS:"
    for index, material in enumerate(scene.materials):
        print "  MATERIAL", index+1
        properties = pyassimp.GetMaterialProperties(material)
        for key in properties:
            print "    %s: %s" % (key, properties[key])
    print
    
    print "TEXTURES:"
    for index, texture in enumerate(scene.textures):
        print "  TEXTURE", index+1
        print "    width:", texture.mWidth
        print "    height:", texture.mHeight
        print "    hint:", texture.achFormatHint
        print "    data (size):", texture.mWidth*texture.mHeight
   
    # Finally release the model
    pyassimp.release(scene)


def main(filename=None):
    filename = filename or DEFAULT_MODEL


    # First initialize the openGL context
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(400,400)
    glutCreateWindow(name)


    load_dae(filename)

    glClearColor(0.,0.,0.,1.)
    glShadeModel(GL_SMOOTH)
    glEnable(GL_CULL_FACE)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    lightZeroPosition = [10.,4.,10.,1.]
    lightZeroColor = [0.8,1.0,0.8,1.0] #green tinged
    glLightfv(GL_LIGHT0, GL_POSITION, lightZeroPosition)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, lightZeroColor)
    glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION, 0.1)
    glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.05)
    glEnable(GL_LIGHT0)

    glutDisplayFunc(display)

    glMatrixMode(GL_PROJECTION)
    gluPerspective(40.,1.,1.,40.)
    glMatrixMode(GL_MODELVIEW)
    gluLookAt(0,0,10,
              0,0,0,
              0,1,0)
    glPushMatrix()
    glutMainLoop()
    return

def tree_exploration(node, depth = 0):

    print("\t" * depth + "Node: " + (node.name if node.name else "[no name]"))
    print("\t" * depth + "Nb children: " + str(len(node.children)))
    print("\t" * depth + "Nb meshes: " + str(len(node.meshes)))
    if node.meshes:
        print("\t" * depth + "\tFirst mesh: " + node.meshes[0].name)
        print("\t" * depth + "\tNb faces in first mesh: " + str(len(node.meshes[0].faces)))

    for child in node.children:
        tree_exploration(child, depth + 1)


def recursive_render(scene, node):

    # save model matrix and apply node transformation
    pushMatrix()
    load_transformation(node.mTransformation)
    for i in node.mNumMeshes:
        glEnableClientState(GL_VERTEX_ARRAY)
        glBindBufferARB(GL_ARRAY_BUFFER_ARB, mesh["vertices"])
        glVertexPointer(3, GL_FLOAT, 0, None)

        glEnableClientState(GL_NORMAL_ARRAY)
        glBindBufferARB(GL_ARRAY_BUFFER_ARB, mesh["normals"])
        glNormalPointer(GL_FLOAT, 0, None)

        glDrawArrays(GL_TRIANGLES,0, mesh["nb_faces"]*3)
        #glDrawElements(GL_TRIANGLES,mesh["nb_faces"]*3,GL_UNSIGNED_SHORT,ArrayDatatype.voidDataPointer(mesh["triangles_data"]))



    popMatrix()

def display():
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glPushMatrix()
    color = [1.0,0.,0.,1.]
    glMaterialfv(GL_FRONT,GL_DIFFUSE,color)
    #glutSolidSphere(2,20,20)
    for mesh in meshes:
        glEnableClientState(GL_VERTEX_ARRAY)
        glBindBufferARB(GL_ARRAY_BUFFER_ARB, mesh["vertices"])
        glVertexPointer(3, GL_FLOAT, 0, None)

        glEnableClientState(GL_NORMAL_ARRAY)
        glBindBufferARB(GL_ARRAY_BUFFER_ARB, mesh["normals"])
        glNormalPointer(GL_FLOAT, 0, None)

        glDrawArrays(GL_TRIANGLES,0, mesh["nb_faces"]*3)
        #glDrawElements(GL_TRIANGLES,mesh["nb_faces"]*3,GL_UNSIGNED_SHORT,ArrayDatatype.voidDataPointer(mesh["triangles_data"]))

    glPopMatrix()
    glutSwapBuffers()
    return

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv)>1 else None)


