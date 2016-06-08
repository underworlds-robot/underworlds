Installation
============

The only mandatory prerequisite is the Python bindings of ``ZeroMQ``.

On Ubuntu/Debian::

    apt-get install python-zmq

``pyassimp``, ``python-OpenGL`` and ``pygame`` are also necessary to use the 3D mesh
loader and the 3D scene viewer. On Ubuntu/Debian::

    apt-get install python-pyassimp python-opengl python-pygame

Then::

    python setup.py install

First tests with underworlds
----------------------------

#. Start the `underworlds` daemon::

    underworlded start

#. Load some model::

    uwds-load testing/res/monkey_mat.blend test

   This loads 3 monkey heads in the ``test`` world.

#. Get a 3D view of this world::

    uwds-view test

   This opens an OpenGL windows that display the content of the ``test`` world. You can
   click on meshes to move them with the keyboard.


.. note::

   If you encounter difficulties installating and/or running underworlds, please
   `fill an issue <https://github.com/severin-lemaignan/underworlds/issues>`__!

