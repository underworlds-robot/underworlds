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

Please refer to the [installation documentation](http://underworlds.readthedocs.io/en/latest/installation.html?highlight=installation).

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

See also
--------

- M.  Naef,  E. Lamboray,  O. Staadt,  and M.  Gross, **The  blue-c  distributed scene graph**
- Bustos, Pablo, et al. **A Unified Internal Representation of the Outer World
  for Social Robotics.** Robot 2015: Second Iberian Robotics Conference. Springer
  International Publishing, 2016.
