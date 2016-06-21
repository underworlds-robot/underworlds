# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: underworlds.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='underworlds.proto',
  package='underworlds',
  syntax='proto3',
  serialized_pb=_b('\n\x11underworlds.proto\x12\x0bunderworlds\"\x14\n\x06\x43lient\x12\n\n\x02id\x18\x01 \x01(\t\"\xa5\x01\n\x04Node\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12#\n\x04type\x18\x03 \x01(\x0e\x32\x15.underworlds.NodeType\x12\x0e\n\x06parent\x18\x04 \x01(\t\x12\x10\n\x08\x63hildren\x18\x05 \x03(\t\x12\x16\n\x0etransformation\x18\x06 \x03(\x02\x12\x13\n\x0blast_update\x18\x08 \x01(\x02\x12\x0f\n\x07physics\x18\x10 \x01(\x08\"\x14\n\x05Nodes\x12\x0b\n\x03ids\x18\x01 \x03(\t\"(\n\x07\x43ontext\x12\x0e\n\x06\x63lient\x18\x01 \x01(\t\x12\r\n\x05world\x18\x02 \x01(\t\"\x14\n\x04Name\x12\x0c\n\x04name\x18\x01 \x01(\t\"\x14\n\x04Size\x12\x0c\n\x04size\x18\x01 \x01(\x05\"B\n\rNodeInContext\x12%\n\x07\x63ontext\x18\x01 \x01(\x0b\x32\x14.underworlds.Context\x12\n\n\x02id\x18\x02 \x01(\t*;\n\x08NodeType\x12\r\n\tUNDEFINED\x10\x00\x12\n\n\x06\x45NTITY\x10\x01\x12\x08\n\x04MESH\x10\x02\x12\n\n\x06\x43\x41MERA\x10\x03\x32\xaa\x02\n\x0bUnderworlds\x12\x30\n\x04Helo\x12\x11.underworlds.Name\x1a\x13.underworlds.Client\"\x00\x12\x38\n\x0bGetNodesLen\x12\x14.underworlds.Context\x1a\x11.underworlds.Size\"\x00\x12\x39\n\x0bGetNodesIds\x12\x14.underworlds.Context\x1a\x12.underworlds.Nodes\"\x00\x12\x38\n\x0bGetRootNode\x12\x14.underworlds.Context\x1a\x11.underworlds.Node\"\x00\x12:\n\x07GetNode\x12\x1a.underworlds.NodeInContext\x1a\x11.underworlds.Node\"\x00\x62\x06proto3')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

_NODETYPE = _descriptor.EnumDescriptor(
  name='NodeType',
  full_name='underworlds.NodeType',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='UNDEFINED', index=0, number=0,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ENTITY', index=1, number=1,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='MESH', index=2, number=2,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='CAMERA', index=3, number=3,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=400,
  serialized_end=459,
)
_sym_db.RegisterEnumDescriptor(_NODETYPE)

NodeType = enum_type_wrapper.EnumTypeWrapper(_NODETYPE)
UNDEFINED = 0
ENTITY = 1
MESH = 2
CAMERA = 3



_CLIENT = _descriptor.Descriptor(
  name='Client',
  full_name='underworlds.Client',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='underworlds.Client.id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=34,
  serialized_end=54,
)


_NODE = _descriptor.Descriptor(
  name='Node',
  full_name='underworlds.Node',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='underworlds.Node.id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='name', full_name='underworlds.Node.name', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='type', full_name='underworlds.Node.type', index=2,
      number=3, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='parent', full_name='underworlds.Node.parent', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='children', full_name='underworlds.Node.children', index=4,
      number=5, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='transformation', full_name='underworlds.Node.transformation', index=5,
      number=6, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='last_update', full_name='underworlds.Node.last_update', index=6,
      number=8, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='physics', full_name='underworlds.Node.physics', index=7,
      number=16, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=57,
  serialized_end=222,
)


_NODES = _descriptor.Descriptor(
  name='Nodes',
  full_name='underworlds.Nodes',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='ids', full_name='underworlds.Nodes.ids', index=0,
      number=1, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=224,
  serialized_end=244,
)


_CONTEXT = _descriptor.Descriptor(
  name='Context',
  full_name='underworlds.Context',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='client', full_name='underworlds.Context.client', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='world', full_name='underworlds.Context.world', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=246,
  serialized_end=286,
)


_NAME = _descriptor.Descriptor(
  name='Name',
  full_name='underworlds.Name',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='underworlds.Name.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=288,
  serialized_end=308,
)


_SIZE = _descriptor.Descriptor(
  name='Size',
  full_name='underworlds.Size',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='size', full_name='underworlds.Size.size', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=310,
  serialized_end=330,
)


_NODEINCONTEXT = _descriptor.Descriptor(
  name='NodeInContext',
  full_name='underworlds.NodeInContext',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='context', full_name='underworlds.NodeInContext.context', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='id', full_name='underworlds.NodeInContext.id', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=332,
  serialized_end=398,
)

_NODE.fields_by_name['type'].enum_type = _NODETYPE
_NODEINCONTEXT.fields_by_name['context'].message_type = _CONTEXT
DESCRIPTOR.message_types_by_name['Client'] = _CLIENT
DESCRIPTOR.message_types_by_name['Node'] = _NODE
DESCRIPTOR.message_types_by_name['Nodes'] = _NODES
DESCRIPTOR.message_types_by_name['Context'] = _CONTEXT
DESCRIPTOR.message_types_by_name['Name'] = _NAME
DESCRIPTOR.message_types_by_name['Size'] = _SIZE
DESCRIPTOR.message_types_by_name['NodeInContext'] = _NODEINCONTEXT
DESCRIPTOR.enum_types_by_name['NodeType'] = _NODETYPE

Client = _reflection.GeneratedProtocolMessageType('Client', (_message.Message,), dict(
  DESCRIPTOR = _CLIENT,
  __module__ = 'underworlds_pb2'
  # @@protoc_insertion_point(class_scope:underworlds.Client)
  ))
_sym_db.RegisterMessage(Client)

Node = _reflection.GeneratedProtocolMessageType('Node', (_message.Message,), dict(
  DESCRIPTOR = _NODE,
  __module__ = 'underworlds_pb2'
  # @@protoc_insertion_point(class_scope:underworlds.Node)
  ))
_sym_db.RegisterMessage(Node)

Nodes = _reflection.GeneratedProtocolMessageType('Nodes', (_message.Message,), dict(
  DESCRIPTOR = _NODES,
  __module__ = 'underworlds_pb2'
  # @@protoc_insertion_point(class_scope:underworlds.Nodes)
  ))
_sym_db.RegisterMessage(Nodes)

Context = _reflection.GeneratedProtocolMessageType('Context', (_message.Message,), dict(
  DESCRIPTOR = _CONTEXT,
  __module__ = 'underworlds_pb2'
  # @@protoc_insertion_point(class_scope:underworlds.Context)
  ))
_sym_db.RegisterMessage(Context)

Name = _reflection.GeneratedProtocolMessageType('Name', (_message.Message,), dict(
  DESCRIPTOR = _NAME,
  __module__ = 'underworlds_pb2'
  # @@protoc_insertion_point(class_scope:underworlds.Name)
  ))
_sym_db.RegisterMessage(Name)

Size = _reflection.GeneratedProtocolMessageType('Size', (_message.Message,), dict(
  DESCRIPTOR = _SIZE,
  __module__ = 'underworlds_pb2'
  # @@protoc_insertion_point(class_scope:underworlds.Size)
  ))
_sym_db.RegisterMessage(Size)

NodeInContext = _reflection.GeneratedProtocolMessageType('NodeInContext', (_message.Message,), dict(
  DESCRIPTOR = _NODEINCONTEXT,
  __module__ = 'underworlds_pb2'
  # @@protoc_insertion_point(class_scope:underworlds.NodeInContext)
  ))
_sym_db.RegisterMessage(NodeInContext)


import grpc
from grpc.beta import implementations as beta_implementations
from grpc.beta import interfaces as beta_interfaces
from grpc.framework.common import cardinality
from grpc.framework.interfaces.face import utilities as face_utilities


class UnderworldsStub(object):

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.Helo = channel.unary_unary(
        '/underworlds.Underworlds/Helo',
        request_serializer=Name.SerializeToString,
        response_deserializer=Client.FromString,
        )
    self.GetNodesLen = channel.unary_unary(
        '/underworlds.Underworlds/GetNodesLen',
        request_serializer=Context.SerializeToString,
        response_deserializer=Size.FromString,
        )
    self.GetNodesIds = channel.unary_unary(
        '/underworlds.Underworlds/GetNodesIds',
        request_serializer=Context.SerializeToString,
        response_deserializer=Nodes.FromString,
        )
    self.GetRootNode = channel.unary_unary(
        '/underworlds.Underworlds/GetRootNode',
        request_serializer=Context.SerializeToString,
        response_deserializer=Node.FromString,
        )
    self.GetNode = channel.unary_unary(
        '/underworlds.Underworlds/GetNode',
        request_serializer=NodeInContext.SerializeToString,
        response_deserializer=Node.FromString,
        )


class UnderworldsServicer(object):

  def Helo(self, request, context):
    """Establish the connection to the server, setting a human-friendly name for
    the client.
    The server returns a unique client ID that must be used in every subsequent
    request to the server.
    """
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def GetNodesLen(self, request, context):
    """Returns the number of nodes in a given world.

    Accepts a context (client ID and world) and returns the number of existing nodes.
    """
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def GetNodesIds(self, request, context):
    """Returns the list of node IDs present in the given world
    """
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def GetRootNode(self, request, context):
    """Returns the root node ID of the given world
    """
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def GetNode(self, request, context):
    """Returns a node from its ID in the given world
    """
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_UnderworldsServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'Helo': grpc.unary_unary_rpc_method_handler(
          servicer.Helo,
          request_deserializer=Name.FromString,
          response_serializer=Client.SerializeToString,
      ),
      'GetNodesLen': grpc.unary_unary_rpc_method_handler(
          servicer.GetNodesLen,
          request_deserializer=Context.FromString,
          response_serializer=Size.SerializeToString,
      ),
      'GetNodesIds': grpc.unary_unary_rpc_method_handler(
          servicer.GetNodesIds,
          request_deserializer=Context.FromString,
          response_serializer=Nodes.SerializeToString,
      ),
      'GetRootNode': grpc.unary_unary_rpc_method_handler(
          servicer.GetRootNode,
          request_deserializer=Context.FromString,
          response_serializer=Node.SerializeToString,
      ),
      'GetNode': grpc.unary_unary_rpc_method_handler(
          servicer.GetNode,
          request_deserializer=NodeInContext.FromString,
          response_serializer=Node.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'underworlds.Underworlds', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))


class BetaUnderworldsServicer(object):
  def Helo(self, request, context):
    """Establish the connection to the server, setting a human-friendly name for
    the client.
    The server returns a unique client ID that must be used in every subsequent
    request to the server.
    """
    context.code(beta_interfaces.StatusCode.UNIMPLEMENTED)
  def GetNodesLen(self, request, context):
    """Returns the number of nodes in a given world.

    Accepts a context (client ID and world) and returns the number of existing nodes.
    """
    context.code(beta_interfaces.StatusCode.UNIMPLEMENTED)
  def GetNodesIds(self, request, context):
    """Returns the list of node IDs present in the given world
    """
    context.code(beta_interfaces.StatusCode.UNIMPLEMENTED)
  def GetRootNode(self, request, context):
    """Returns the root node ID of the given world
    """
    context.code(beta_interfaces.StatusCode.UNIMPLEMENTED)
  def GetNode(self, request, context):
    """Returns a node from its ID in the given world
    """
    context.code(beta_interfaces.StatusCode.UNIMPLEMENTED)


class BetaUnderworldsStub(object):
  def Helo(self, request, timeout, metadata=None, with_call=False, protocol_options=None):
    """Establish the connection to the server, setting a human-friendly name for
    the client.
    The server returns a unique client ID that must be used in every subsequent
    request to the server.
    """
    raise NotImplementedError()
  Helo.future = None
  def GetNodesLen(self, request, timeout, metadata=None, with_call=False, protocol_options=None):
    """Returns the number of nodes in a given world.

    Accepts a context (client ID and world) and returns the number of existing nodes.
    """
    raise NotImplementedError()
  GetNodesLen.future = None
  def GetNodesIds(self, request, timeout, metadata=None, with_call=False, protocol_options=None):
    """Returns the list of node IDs present in the given world
    """
    raise NotImplementedError()
  GetNodesIds.future = None
  def GetRootNode(self, request, timeout, metadata=None, with_call=False, protocol_options=None):
    """Returns the root node ID of the given world
    """
    raise NotImplementedError()
  GetRootNode.future = None
  def GetNode(self, request, timeout, metadata=None, with_call=False, protocol_options=None):
    """Returns a node from its ID in the given world
    """
    raise NotImplementedError()
  GetNode.future = None


def beta_create_Underworlds_server(servicer, pool=None, pool_size=None, default_timeout=None, maximum_timeout=None):
  request_deserializers = {
    ('underworlds.Underworlds', 'GetNode'): NodeInContext.FromString,
    ('underworlds.Underworlds', 'GetNodesIds'): Context.FromString,
    ('underworlds.Underworlds', 'GetNodesLen'): Context.FromString,
    ('underworlds.Underworlds', 'GetRootNode'): Context.FromString,
    ('underworlds.Underworlds', 'Helo'): Name.FromString,
  }
  response_serializers = {
    ('underworlds.Underworlds', 'GetNode'): Node.SerializeToString,
    ('underworlds.Underworlds', 'GetNodesIds'): Nodes.SerializeToString,
    ('underworlds.Underworlds', 'GetNodesLen'): Size.SerializeToString,
    ('underworlds.Underworlds', 'GetRootNode'): Node.SerializeToString,
    ('underworlds.Underworlds', 'Helo'): Client.SerializeToString,
  }
  method_implementations = {
    ('underworlds.Underworlds', 'GetNode'): face_utilities.unary_unary_inline(servicer.GetNode),
    ('underworlds.Underworlds', 'GetNodesIds'): face_utilities.unary_unary_inline(servicer.GetNodesIds),
    ('underworlds.Underworlds', 'GetNodesLen'): face_utilities.unary_unary_inline(servicer.GetNodesLen),
    ('underworlds.Underworlds', 'GetRootNode'): face_utilities.unary_unary_inline(servicer.GetRootNode),
    ('underworlds.Underworlds', 'Helo'): face_utilities.unary_unary_inline(servicer.Helo),
  }
  server_options = beta_implementations.server_options(request_deserializers=request_deserializers, response_serializers=response_serializers, thread_pool=pool, thread_pool_size=pool_size, default_timeout=default_timeout, maximum_timeout=maximum_timeout)
  return beta_implementations.server(method_implementations, options=server_options)


def beta_create_Underworlds_stub(channel, host=None, metadata_transformer=None, pool=None, pool_size=None):
  request_serializers = {
    ('underworlds.Underworlds', 'GetNode'): NodeInContext.SerializeToString,
    ('underworlds.Underworlds', 'GetNodesIds'): Context.SerializeToString,
    ('underworlds.Underworlds', 'GetNodesLen'): Context.SerializeToString,
    ('underworlds.Underworlds', 'GetRootNode'): Context.SerializeToString,
    ('underworlds.Underworlds', 'Helo'): Name.SerializeToString,
  }
  response_deserializers = {
    ('underworlds.Underworlds', 'GetNode'): Node.FromString,
    ('underworlds.Underworlds', 'GetNodesIds'): Nodes.FromString,
    ('underworlds.Underworlds', 'GetNodesLen'): Size.FromString,
    ('underworlds.Underworlds', 'GetRootNode'): Node.FromString,
    ('underworlds.Underworlds', 'Helo'): Client.FromString,
  }
  cardinalities = {
    'GetNode': cardinality.Cardinality.UNARY_UNARY,
    'GetNodesIds': cardinality.Cardinality.UNARY_UNARY,
    'GetNodesLen': cardinality.Cardinality.UNARY_UNARY,
    'GetRootNode': cardinality.Cardinality.UNARY_UNARY,
    'Helo': cardinality.Cardinality.UNARY_UNARY,
  }
  stub_options = beta_implementations.stub_options(host=host, metadata_transformer=metadata_transformer, request_serializers=request_serializers, response_deserializers=response_deserializers, thread_pool=pool, thread_pool_size=pool_size)
  return beta_implementations.dynamic_stub(channel, 'underworlds.Underworlds', cardinalities, options=stub_options)
# @@protoc_insertion_point(module_scope)
