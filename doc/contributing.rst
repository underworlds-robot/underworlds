Developpers documentation
=========================

Re-compiling the gRPC transport layer
-------------------------------------

Underworlds uses gRPC as transport layer. The RPC services and messages are
defined in `underworlds.proto`, at the root of the project.

If you modify the `protobuf` interface description, you need to recompile the
Python bindings. Once gRPC is installed on your system, this can be achieved by
running::

    protoc --python_out=. --grpc_out=. --plugin=protoc-gen-grpc=`which grpc_python_plugin` underworlds.proto


