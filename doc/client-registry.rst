Clients registry
================

This page lists the main 'official' ``underworlds`` clients, that are of general use.

Several core clients are `hosted directly in the main underworlds repository
<https://github.com/underworlds-robot/underworlds/tree/master/bin>`_. The
others are typically hosted under the ``underworlds-robot`` `GitHub
organisation <https://github.com/underworlds-robot>`_.

Core clients
------------

The core clients are `hosted directly in the main underworlds repository
<https://github.com/underworlds-robot/underworlds/tree/master/bin>`_.


- ``uwds {ls, load, edit, show}``: simple command-line tools to inspect and
  manipulate the ``underworlds`` network. Check their individual help pages for
  details.

- ``uwds view``: a 3D renderer to display and inspect ``underworlds`` worlds:

.. figure:: images/env+robot+human.jpg
   :width: 70%

   Screenshot of ``uwds view``. Cameras are attached to the robots
   and the human faces, and can be used to check whether objects are visible
   from the point of view of a given agent.

- ``uwds visibility``: compute the list of visible objects, from each camera's view point.
- ``uwds tf``: bridges `ROS tf <http://wiki.ros.org/tf>`_ with ``underworlds``
  -- creates/updates ROS ``tf`` frames in a given ``underworlds`` world, with
  the option to select the desired ``tf`` frames using a regex.

.. note::

    Check as well the `core-tools` page for more details.

Community clients
-----------------

*Check each client's README for details regarding usage/installation.*

- `perspective_filter <https://github.com/underworlds-robot/perspective_filter>`_: perspective taking & beliefs computation

- `robot_monitor <https://github.com/underworlds-robot/robot_monitor>`_: monitor the robot from `/tf` and an input world to provide an Underworlds output world with the input objects and the robot 

- `env_provider <https://github.com/underworlds-robot/env_provider>`_: create an ``underworlds`` world from a static description of the environment 

- `allocentric_monitor <https://github.com/underworlds-robot/allocentric_monitor>`_

- `ar_object_provider <https://github.com/underworlds-robot/ar_object_provider>`_: add ``ar_tag`` objects to the given Underworlds world 

- `physics_filter <https://github.com/underworlds-robot/physics_filter>`_: ``underworlds`` filter that use Bullet RT physics simulation to produce the near future of the intput world 
