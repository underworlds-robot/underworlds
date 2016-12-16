Installation
============

Ubuntu/Debian
-------------

The only mandatory prerequisite is the Python bindings of ``gRPC``.

On Ubuntu/Debian::

    pip install grpcio

``pyassimp``, ``python-OpenGL`` and ``pygame`` are also necessary to use the 3D mesh
loader and the 3D scene viewer. On Ubuntu/Debian::

    apt-get install python-pyassimp python-opengl python-pygame

Then::

    python setup.py install
	
Windows
-------

You will need to install python 2.7.x (where x is over version 9 otherwise pip
will also need to be installed seperately). Make sure to add python to your 
system path. ``gRPC`` and ``numpy`` is necessary for undeworlds to work. To install 
gRPC and numpy run the following from your command prompt::

	python -m pip install grpcio
	python -m pip install numpy

In your underworld directory run the following command::

	python setup.py install

Ensure that the ``tmp`` folder exists in the C:\\ directory.

The following is optional but you will most likely want to install these to
allow you to load objects and view the 3D world. This will require ``CMake`` and 
``Assimp``:

https://github.com/assimp/assimp

https://github.com/assimp/assimp/blob/master/

Install ``pyassimp``::

	python -m pip install pyassimp

You will need to copy the assimp dll from where has been compiled into::

	<Python Dir>\Lib\site-packages\pyassimp

Install ``pygame``, ``PyOpenGL`` and ``twisted``::

	python -m pip install pygame
	python -m pip install PyOpenGL
	python -m pip install twisted

First tests with underworlds
----------------------------

1. Start the `underworlds` daemon:

  - On Ubuntu/Debian::

    underworlded start

  - On Windows (Note as well that on windows you need to run these scripts from within the bin folder in your underworlds directory)::

    underworlded foreground

	
2. Load some model::

    uwds-load testing/res/monkey_mat.blend test

   This loads 3 monkey heads in the ``test`` world.

3. Get a 3D view of this world::

    uwds-view test

   This opens an OpenGL windows that display the content of the ``test`` world. You can
   click on meshes to move them with the keyboard.


.. note::

   If you encounter difficulties installating and/or running underworlds, please
   `fill an issue <https://github.com/severin-lemaignan/underworlds/issues>`__!
