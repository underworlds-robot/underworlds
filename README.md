Underworlds: Geometric & Temporal Representation for Robots
===========================================================

[![Documentation Status](https://readthedocs.org/projects/underworlds/badge/?version=latest)](http://underworlds.readthedocs.org)

Description
-----------

Underworlds is a distributed and lightweight framework that aims at sharing
between clients parallel models of the physical world surrounding a robot.

The clients can be geometric reasoners (that compute topological relations
between objects), motion planner, event monitors, viewers... any software that
need to access a geometric (based on 3D meshes of objects) and/or temporal
(based on events) view of the world.

One of the main specific feature of Underworlds is the ability to store many
parallel worlds: past models of the environment, future models, models with
some objects filtered out, models that are physically consistent, etc.

This package provides the library, and a small set of core clients that are
useful for inspection and debugging.

Installation
------------

The only mandatory prerequisite is the Python bindings of `gRPC`:
```
> pip install grpcio
```

`pyassimp`, `python-OpenGL` and `pygame` are also necessary to use the 3D mesh
loader and the 3D scene viewer (`apt-get install python-pyassimp python-opengl
python-pygame`).

Then:

```
> python setup.py install
```

Installation on windows
-----------------------



First tests with Underworlds
----------------------------

1. Start the `underworlds` daemon:

```
> underworlded start
```

2. Load some model:

```
> uwds-load testing/res/monkey_mat.dae test
```

This loads 3 monkey heads in the 'test' world.

3. Get a 3D view of this world:

```
> uwds-view test
```

Open an OpenGL windows that display the content of the 'test' world. You can
click on meshes to move them with the keyboard.

Running the unit-tests
----------------------

Underworlds provides a few unit-tests. Run them with:

```
> cd testing
> ./run_test.py
```

Documentation
-------------

[Head to readthedocs](http://underworlds.readthedocs.org). Sparse for now.

