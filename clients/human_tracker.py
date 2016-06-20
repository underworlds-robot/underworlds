#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import logging; logger = logging.getLogger("underworlds.human_tracker")

import sys
import math
import numpy

from openni import openni2, nite2, utils


import underworlds
from underworlds.helpers import transformations
from underworlds.types import Node, ENTITY
from underworlds.tools.loader import ModelLoader

# Attention!! The labels for the right and left sides are inverted so that when
# the user move the left hand, it also moves the left hand of the 'avatar'
# See page 13 of http://www.openni.ru/wp-content/uploads/2013/02/NITE-Algorithms.pdf
# for the details.
joints = {"head":       nite2.JointType.NITE_JOINT_HEAD,
          "neck":       nite2.JointType.NITE_JOINT_NECK,
          "torso":      nite2.JointType.NITE_JOINT_TORSO,
          "r_shoulder": nite2.JointType.NITE_JOINT_LEFT_SHOULDER,
          "l_shoulder": nite2.JointType.NITE_JOINT_RIGHT_SHOULDER,
          "r_elbow":    nite2.JointType.NITE_JOINT_LEFT_ELBOW,
          "l_elbow":    nite2.JointType.NITE_JOINT_RIGHT_ELBOW,
          "r_hand":     nite2.JointType.NITE_JOINT_LEFT_HAND,
          "l_hand":     nite2.JointType.NITE_JOINT_RIGHT_HAND
          }


def transformation_matrix(user, joint_code):
    joint = user.skeleton.joints[joint_code]

    #confidence = head.positionConfidence

    translation = (joint.position.x/1000.,
                   joint.position.y/1000.,
                   joint.position.z/1000.)


    translation_mat = transformations.translation_matrix(translation)

    orientation = (joint.orientation.x, 
                    joint.orientation.y,
                    joint.orientation.z,
                    joint.orientation.w)

    rotation_mat = transformations.quaternion_matrix(orientation)

    # mirror back the skeleton along the X axis, as the freenect driver mirrors the
    # RGBD image by default
    mirror_mat = transformations.reflection_matrix((0,0,0),(1,0,0))

    return numpy.dot(mirror_mat, numpy.dot(translation_mat, rotation_mat))

def process_frame(frame):

    if len(frame.users):
        for user in frame.users:
            if user.is_new():
                logger.info("New human detected! Calibrating...")
                userTracker.start_skeleton_tracking(user.id)
            elif user.skeleton.state == nite2.SkeletonState.NITE_SKELETON_TRACKED:

                return {name: transformation_matrix(user, joint_code) for name, joint_code in joints.items()}


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("world", help="Underworlds world to monitor")
    #parser.add_argument("-d", "--debug", help="run in interactive, debug mode", action="store_true")
    args = parser.parse_args()
    

    ### OpenNI/NiTE initialization
    openni2.initialize()
    nite2.initialize()

    logger.info("Opening a freenect device...")
    dev = openni2.Device.open_any()
    info = dev.get_device_info()
    logger.info("Device <%s %s> successfully opened." % (info.vendor, info.name))

    logger.info("Loading the NiTE user tracker...")
    try:
        userTracker = nite2.UserTracker(dev)
    except utils.NiteError as ne:
        logger.error("Unable to start the NiTE human tracker. Check "
                    "the error messages in the console. Model data "
                    "(s.dat, h.dat...) might be missing.")
        sys.exit(-1)
    logger.info("User tracker loaded.")

    logger.info("Now waiting for humans...")
    #############



    with underworlds.Context("Human tracker") as ctx:

        world = ctx.worlds[args.world]
        nodes = world.scene.nodes

        camera = Node("kinect", ENTITY)

        translation_cam=transformations.translation_matrix((1,0,0.5))

        # According to http://www.openni.ru/wp-content/uploads/2013/02/NITE-Algorithms.pdf
        # the sensor is oriented as follow:
        # " +X points to the right of the, +Y points up, and +Z
        # points in the direction of increasing depth."
        rotation_cam=transformations.euler_matrix(math.pi/2,0,math.pi/2)

        camera.transformation = numpy.dot(translation_cam, rotation_cam)
        camera.parent = world.scene.rootnode.id
        nodes.append(camera)

        # Load the mannequin mesh into underworlds and get back the list of
        # underworlds nodes
        bodypartslist = ModelLoader(args.world).load("../share/mannequin.blend",
                                                     ctx=ctx,
                                                     root=camera)

        human_nodes = {node.name:node for node in bodypartslist}

        try:
            while True:

                frame = userTracker.read_frame()
                #logger.info("%s humans detected" % len(frame.users))

                humanparts = process_frame(frame)

                if humanparts is not None:
                    for name, transformation in humanparts.items():
                        
                        node = human_nodes[name]
                        node.transformation = transformation
                        nodes.update(node)


        except KeyboardInterrupt:
            logger.info("Quitting...")

        ## Clean up
        for _, node in human_nodes.items():
            nodes.remove(node)

        nodes.remove(camera)

    nite2.unload()
    openni2.unload()
    logger.info("Bye!")
