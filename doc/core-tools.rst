underwords Core Tools
=====================

underworlds comes with a set of core tools to manage and visualize the system.

underworlded
~~~~~~~~~~~~

``underworlded`` is the daemon that maintain and distribute the worlds amongst
the clients' network. It must be running prior to any other underworlds
applications::

    $ underworlded start|stop|restart

For debugging purposes, you can start it in the foreground::

    $ underworlded foreground


.. note::

    The ``underworlded`` server does not have to run on the same physical machine as the clients.
    In this case, you need to export the environment variable ``UWDS_SERVER=<host>[:<port>]`` prior to
    the launch of each of the client.

uwds-ls
~~~~~~~

``uwds-ls`` simply lists on the command line all the worlds that currently
existing, along with the nodes they contains.

Usage::

    $ uwds-ls

uwds-explorer -- Visualization of the underworlds network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``uwds-explorer`` is a small gtk application that displays a graph of the
underworlds' network topology.

uwds-view -- 3D visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``uwds-view`` can be used to visualize in 3D (and to a limited extend, interact
with) a world::

    $ uwds-view <world>


* Use the mouse and the arrow keys to navigate.
* Clicking on a mesh selects it. You can then move the object with the arrow
  keys.
* Press :kbd:`s` to take a screenshot.
* Press :kbd:`f` to toggle fullscreen.
* Press :kbd:`tab` to cycle through available cameras (if more than one!)
* :kbd:`esc` quits

.. note::

    The `source of uwds-view
    <https://github.com/severin-lemaignan/underworlds/tree/master/bin/uwds-view>`__
    shows how the datastructures provided by underworlds can be used for
    realtime 3D rendering with OpenGL. This may be a useful starting point for other
    rendering applications.


uwds-load -- Loading of 3D models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can easily populate a world with 3D meshes by using ``uwds-load``::

    $ uwds-load <3d model> <world>

Many 3D models format are recognized (the loader relies on `Assimp
<http://assimp.org/main_features_formats.html>`__). You can load without trouble whole scene,
with as many objects or cameras as you like.

