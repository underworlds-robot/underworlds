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


def process_frame(frame):

    if len(frame.users):
        for user in frame.users:
            if user.is_new():
                logger.info("New human detected! Calibrating...")
                userTracker.start_skeleton_tracking(user.id)
            elif user.skeleton.state == nite2.SkeletonState.NITE_SKELETON_TRACKED:
                head = user.skeleton.joints[nite2.JointType.NITE_JOINT_HEAD]

                #confidence = head.positionConfidence

                translation = (head.position.x/1000.,
                               head.position.y/1000.,
                               head.position.z/1000.)


                translation_mat = transformations.translation_matrix(translation)

                orientation = (head.orientation.x, 
                            head.orientation.y,
                            head.orientation.z,
                            head.orientation.w)

                rotation_mat = transformations.quaternion_matrix(orientation)

                return numpy.dot(translation_mat, rotation_mat)


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
        rotation_cam=transformations.euler_matrix(math.pi/2,0,0)

        camera.transformation = numpy.dot(translation_cam, rotation_cam)
        camera.parent = world.scene.rootnode.id
        nodes.append(camera)

        head = Node("head", ENTITY)
        head.parent = camera.id
        nodes.append(head)

        try:
            while True:

                frame = userTracker.read_frame()
                #logger.info("%s humans detected" % len(frame.users))

                transformation = process_frame(frame)

                if transformation is not None:
                    head.transformation = transformation
                    nodes.update(head)


        except KeyboardInterrupt:
            logger.info("Quitting...")

        nodes.remove(head)
        nodes.remove(camera)

    nite2.unload()
    openni2.unload()
    logger.info("Bye!")
