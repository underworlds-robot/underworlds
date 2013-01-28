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
      scripts=['bin/' + f for f in os.listdir('scripts')],
      packages=['underworlds', 'underworlds.helpers', 'underworlds.tools'],
      data_files=[('share/doc/underworlds', ['LICENSE', 'README'])],
      requires=["pyassimp"]
      )
