The client-server protocol
==========================

``underwords`` relies on `gRPC <https://grpc.io/>`_ for communication and
synchronisation between the clients and the server.

The protocol is defined using the `Protocol Buffers
<https://developers.google.com/protocol-buffers/>`_ IDL. The interface
definition can be found in `underworlds.proto
<https://github.com/severin-lemaignan/underworlds/blob/master/underworlds.proto>`_
