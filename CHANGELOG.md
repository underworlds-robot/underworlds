underworlds next
================

(not yet released)

- nodes can now have a list of arbitrary properties. Standard/recommended
  properties (like the bounding box for meshes or the field of view for cameras)
  are defined in [the properties registry](doc/properties-registry.rst).
- support for batch update/deletion of nodes. This should significantly increase
  performances for clients touching many nodes at each iterations.
- fixed 2 annoying bugs with parenting (in particular, deleting a node with
  children would essentially corrupt the children) and added extensive
  unit-tests for various parenting-related operations.

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

