# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

from xiaoyuan_tts.v1 import xiaoyuan_tts_v1_api_pb2 as xiaoyuan__tts_dot_v1_dot_xiaoyuan__tts__v1__api__pb2


class APIStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.Exec = channel.unary_unary(
        '/brain.nlp.api.xiaoyuanTTS.v1.API/Exec',
        request_serializer=xiaoyuan__tts_dot_v1_dot_xiaoyuan__tts__v1__api__pb2.ExecReq.SerializeToString,
        response_deserializer=xiaoyuan__tts_dot_v1_dot_xiaoyuan__tts__v1__api__pb2.ExecResp.FromString,
        )


class APIServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def Exec(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_APIServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'Exec': grpc.unary_unary_rpc_method_handler(
          servicer.Exec,
          request_deserializer=xiaoyuan__tts_dot_v1_dot_xiaoyuan__tts__v1__api__pb2.ExecReq.FromString,
          response_serializer=xiaoyuan__tts_dot_v1_dot_xiaoyuan__tts__v1__api__pb2.ExecResp.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'brain.nlp.api.xiaoyuanTTS.v1.API', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
