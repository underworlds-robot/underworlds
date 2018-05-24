import unittest
import time

import os.path as path
import underworlds
import underworlds.server
from underworlds.tools.edit import *

class TestEditTools(unittest.TestCase):
    
    # workaround for https://github.com/grpc/grpc/issues/14088
    @classmethod
    def setUpClass(cls):
        cls.server = underworlds.server.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop(1).wait()

    def setUp(self):
        # workaround for https://github.com/grpc/grpc/issues/14088
        #self.server = underworlds.server.start()

        self.ctx = underworlds.Context("unittest - edit tools")

        # workaround for https://github.com/grpc/grpc/issues/14088
        self.ctx.reset()
        
    def test_edit_meshes(self):
        world = self.ctx.worlds["base"]
        
        #Test creation of Box Mesh
        mesh_id1 = None
        mesh_id1 = create_box_mesh("base", 3, 2, 1)
        
        self.assertTrue(mesh_id1 is not None)
        
        #Test creation of a Mesh node with a mesh
        create_mesh_node("base", "testNode", mesh_id1)
        tMeshNode = world.scene.nodebyname("testNode")
        
        self.assertEqual(len(tMeshNode), 1)
        self.assertTrue(unicode(mesh_id1[0], "utf-8") in tMeshNode[0].properties["mesh_ids"]) #Check the mesh is in the Mesh Node.
        
        #Test loading a Mesh
        mesh_id2 = None
        mesh_id2 = load_mesh("base", path.join("res","tree.blend"))
        
        self.assertTrue(mesh_id2 is not None)
        
        #Test adding a Mesh to an existing Node
        add_mesh_to_node("base", tMeshNode[0].id, mesh_id2)
        tMeshNode = world.scene.nodebyname("testNode")
        
        self.assertEqual(len(tMeshNode), 1) #Not created an additional node.
        self.assertEqual(len(tMeshNode[0].properties["mesh_ids"]), len(mesh_id2) + len(mesh_id1)) #Original Meshes have not been removed and new meshes added.
        self.assertTrue(unicode(mesh_id2[0], "utf-8") in tMeshNode[0].properties["mesh_ids"]) #New mesh is in the Mesh node.
        
        #Test removing meshes from Node
        for mesh in mesh_id1:
            remove_mesh("base", tMeshNode[0].id, mesh)
            
        tMeshNode = world.scene.nodebyname("testNode")
        
        self.assertEqual(len(tMeshNode), 1)
        self.assertEqual(len(tMeshNode[0].properties["mesh_ids"]), len(mesh_id2)) #Parity check on number of meshes.
        self.assertFalse(unicode(mesh_id1[0], "utf-8") in tMeshNode[0].properties["mesh_ids"]) #Check Mesh has been removed.
        
        #Test removing final mesh from Node - deleting the node
        meshNodeID = tMeshNode[0].id
        for mesh in mesh_id2:
            remove_mesh("base", tMeshNode[0].id, mesh)
            
        self.assertEqual(len(world.scene.nodes), 1) #Only the root node should be left.
        self.assertFalse(tMeshNode[0] in world.scene.nodes)
        
    def test_edit_nodes(self):
        world = self.ctx.worlds["base"]
        
        #Test creation of an Entity node
        create_entity_node("base", "EntityParent")
        tPEntityNode = world.scene.nodebyname("EntityParent")
        
        self.assertEqual(len(tPEntityNode), 1)
        
        #Create node with non-root parent
        create_entity_node("base", "EntityChild", tPEntityNode[0].id)
        tCEntityNode = world.scene.nodebyname("EntityChild")
        
        self.assertEqual(len(tCEntityNode), 1)
        self.assertEqual(tPEntityNode[0].id, tCEntityNode[0].parent)
        
        #Change parent of node
        set_parent("base", tCEntityNode[0].id, "root")
        tCEntityNode = world.scene.nodebyname("EntityChild")
        
        self.assertEqual(len(tCEntityNode), 1)
        self.assertEqual(world.scene.rootnode.id, tCEntityNode[0].parent)
        
        #Remove node
        remove_node("base", tCEntityNode[0].id)
        tPEntityNode = world.scene.nodebyname("EntityParent")
        
        self.assertEqual(len(world.scene.nodes), 2) #Only root and EntityParent should remain
        self.assertTrue(tPEntityNode[0] in world.scene.nodes)
        self.assertFalse(tCEntityNode[0] in world.scene.nodes)
        
    def test_edit_camera(self):
        world = self.ctx.worlds["base"
        
        #Test creation of a Camera node
        create_camera_node("base", "testCamera", aspect=1, horizontalfov=2)
        tCameraNode = world.scene.nodebyname("testCamera")
        
        self.assertEqual(len(tCameraNode), 1)
        self.assertEqual(tCameraNode[0].properties["aspect"], 1)
        self.assertEqual(tCameraNode[0].properties["horizontalfov"], 2)
        
    def tearDown(self):
        self.ctx.close()

def test_suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEditTools)
    return suite

if __name__ == '__main__':
    unittest.main()
