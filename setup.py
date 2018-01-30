 # -*- coding: utf-8 -*-
import os
from setuptools import setup

setup(name='underworlds',
      version='0.2.1',
      license='ISC',
      description='A framework for geometric and temporal representation of robotic worlds',
      long_description="""underworlds is a **distributed and lightweight framework** that facilitates
**building and sharing models of the physical world** surrounding a robot
amongst independent software modules.

These modules can be for instance geometric reasoners (that compute topological
relations between objects), motion planner, event monitors, viewers... any
software that need to access a **geometric** (based on 3D meshes of objects)
and/or **temporal** (based on events) view of the world.

One of the main feature of underworlds is the ability to store many
*parallel* worlds: past models of the environment, future models, models with
some objects filtered out, models that are physically consistent, etc.

This package provides the underworlds server, a Python client library, and a set
of tools to interact with the system (viewers, scene loader, ROS bridge, etc.).

A handful of useful example applications are also provided, like skeleton
tracking (using OpenNI) or visibility tracking.""",
      author='Séverin Lemaignan',
      author_email='severin.lemaignan@plymouth.ac.uk',
      url='https://github.com/severin-lemaignan/underworlds',
      project_urls={
          "Bug Tracker": "https://github.com/severin-lemaignan/underworlds/issues",
          "Documentation": "https://underworlds.readthedocs.io/",
          "Source Code": "https://github.com/severin-lemaignan/underworlds"},
      package_dir = {'': 'src'},
      scripts=['bin/' + f for f in os.listdir('bin')],
      packages=['underworlds', 'underworlds.helpers', 'underworlds.tools'],
      data_files=[('share/doc/underworlds', ['LICENSE', 'README.md'])],
      install_requires=["pyassimp","grpcio","numpy","argcomplete"]
      )
