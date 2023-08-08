import io
import tempfile
from TTS.api import TTS
from pydub import AudioSegment

class TTSTalker():
    def __init__(self) -> None:
        model_name = TTS.list_models()[0]
        self.tts = TTS(model_name)

    def test(self, text, language='en'):

        tempf  = tempfile.NamedTemporaryFile(
                delete = False,
                suffix = ('.'+'wav'),
            )

        self.tts.tts_to_file(text, speaker=self.tts.speakers[0], language=language, file_path=tempf.name)

        return tempf.name
    
class TTSTalker1():
    def __init__(self) -> None:
        import grpc
        from .xiaoyuan_tts.v1 import xiaoyuan_tts_v1_api_pb2,xiaoyuan_tts_v1_api_pb2_grpc
        self.xiaoyuan_tts_v1_api_pb2 = xiaoyuan_tts_v1_api_pb2
        channel = grpc.insecure_channel('47.103.98.63:59000')
        self.tts_stub = xiaoyuan_tts_v1_api_pb2_grpc.APIStub(channel)
        self.tmp = './results/temp.wav'

    def test(self, text, language='en',return_file=False):
        if return_file:
            self.getTTsResult(text)
            return self.tmp
        return self.getTTsResult(text)
    
    def getTTsResult(self, robotText, tts_id:str='others', ues_thread=False, return_file=False):
        wav_data = self.tts_stub.Exec(self.xiaoyuan_tts_v1_api_pb2.ExecReq(conversation_id="120",user_id="1",text=robotText)).wav_data # 接收转码得到字节数据
        if return_file:
            with open('./results/temp.wav',"wb+") as f: # 写入文件
                f.write(wav_data)
        else:
            return AudioSegment.from_file(io.BytesIO(wav_data))
        
class TTSTalker_API():
    def __init__(self) -> None:
        self.origin_talker = TTSTalker()
        self.xiaoyuan_talker = TTSTalker1()
        
    def test(self, text, talker=0):
        if talker==0:
            return self.xiaoyuan_talker.test(text)
        elif talker==1:
            return self.origin_talker.test(text)

if __name__ == '__main__':
    import time     
    tts = TTSTalker_API()
    start = time.time()
    tts.test('"这个TTS到底快不快阿"') # 1.03s
    print('cost time : ',time.time()-start)