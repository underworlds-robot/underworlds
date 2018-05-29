*this file only list the major, user-facing, changes. See git-log for the full
list.*

underworlds 0.3.0
=================

Released on: 29 May 2018

Contributors: see AUTHORS

- nodes can now have a list of arbitrary properties. Standard/recommended
  properties (like the bounding box for meshes or the field of view for cameras)
  are defined in [the properties registry](doc/properties-registry.rst).
- support for batch update/deletion of nodes. This should significantly increase
  performances for clients touching many nodes at each iterations.
- new major filters, including a [Bullet-based physics
  filter](https://github.com/underworlds-robot/physics_filter) and a
  [user-perspective-based
  filter](https://github.com/underworlds-robot/perspective_filter). A new
  [documentation
  page](https://github.com/underworlds-robot/underworlds/blob/master/doc/client-registry.rst)
  lists available 'official' clients.
- major rewrite of `uwds edit`, adding several sub-tools to reparent, attach
  meshes, etc. (C Wallbridge)
- many improvements wrt to spatial relations. It is now a [Python
  module](https://github.com/underworlds-robot/underworlds/blob/master/src/underworlds/tools/spatial_relations.py)
  that can be used by all clients.
- fixed 2 annoying bugs with parenting (in particular, deleting a node with
  children would essentially corrupt the children) and added extensive
  unit-tests for various parenting-related operations.
- tons of other fixes all accross the board

underworlds 0.2.1
=================

Released on: 25 Jan 2018

Changes since last version:

- minor updates to the setuptools (setup.py) and upload to PyPI for
  easy installation with `pip install underworlds`.

underworlds 0.2
===============

Released on: 25 Jan 2018

Changes since last version:

- uses (Protocol Buffer)[https://developers.google.com/protocol-buffers/] as an
  IDL to explicitely define the `underworlds` communication API (cf
  [underworlds.proto](underworlds.proto))
- uses Google's [gRPC](https://grpc.io/) RPC mechanism, providing
  cross-platform, cross-language support
- many new unit-tests
- added continuous integration support on GItHub, using travis
- large rewrite of the 3D viewer client
- new client to bridge `underworlds` and ROS: it automatically mirror ROS TF
  frames in `underworlds`
- the command-line interface has been revamped, and all the command as basic
  clients are available as sub-commands of the `uwds` tool (like `uwds start` to
  start the server, `uwds ls` to list existing worlds, etc). Type `uwds --help`
  to learn more
- Python3 support

Work in progress:

- the protocol will be updated to only allow max one writer to a world at a
  time. This should simply the code, and prevent a large range of concurrency issues.
- the C++ API has been started, but is not yet usable
- an initial client for computation of spatial relations has been added. Much
  remain to be done, though.

**Please note that the `underworlds` protocol, as defined in `underworlds.proto`
is not considered stable yet.**

underworlds 0.1
===============

Released on: 24 Apr 2016

Initial version, using zeroMQ as transport between the clients and the server.

