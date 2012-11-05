 # -*- coding: utf-8 -*-
import os
from distutils.core import setup

setup(name='underworlds',
      version='0.1',
      license='ISC',
      description='A framework for geometric and temporal representation of robotic worlds',
      author='Séverin Lemaignan',
      author_email='slemaign@laas.fr',
      url='http://www.openrobots.org/underworlds',
      package_dir = {'': 'src'},
      scripts=['scripts/underworlds'],
      packages=['underworlds', 'underworlds.helpers'],
      data_files=[('share/doc/underworlds', ['LICENSE'])],
      requires=["pyassimp"]
      )
