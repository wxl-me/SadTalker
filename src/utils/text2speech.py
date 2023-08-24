import io
import tempfile
from TTS.api import TTS
from pydub import AudioSegment
import grpc,requests,base64,json
from .xiaoyuan_tts.v1 import xiaoyuan_tts_v1_api_pb2,xiaoyuan_tts_v1_api_pb2_grpc

def rvc_transform(audio_data, rvc):
    rvc = int(rvc)
    if rvc==0:
        return audio_data
    url = 'http://192.168.102.23:8003/api/rvc/v2v'
    rvc_req = requests.post(url, json={"input_audio":base64.b64encode(audio_data).decode(), "f0_up_key":str(rvc)})   
    b64 = json.loads(rvc_req.content)['audio_data']
    return base64.b64decode(b64)

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
        self.channel = '47.103.98.63:59000'
        self.tmp = './results/temp.wav'

    def test(self, text, return_file=False, rvc=0):
        tts_stub = xiaoyuan_tts_v1_api_pb2_grpc.APIStub(grpc.insecure_channel(self.channel))
        wav_data = tts_stub.Exec(xiaoyuan_tts_v1_api_pb2.ExecReq(conversation_id="120",user_id="1",text=text)).wav_data # 接收转码得到字节数据 
        wav_data = rvc_transform(wav_data,rvc=rvc)
        if return_file:
            with open(self.tmp,"wb+") as f: # 写入文件
                f.write(wav_data)
            return self.tmp
        else:
            return AudioSegment.from_file(io.BytesIO(wav_data))
        

class TTSTalker2():
    def __init__(self) -> None:
        self.channel = 'http://192.168.102.23:7860'
        self.tmp = './results/temp.wav'

    def test(self,text, talker=133, rvc=0, return_file=False):
        url = f"{self.channel}/voice/vits?text={text}&id={talker}"
        r = requests.get(url)
        if r.status_code == 200:
            wav_data = r.content
            wav_data = rvc_transform(wav_data,rvc=rvc)
            if return_file:
                with open(self.tmp,"wb+") as f: # 写入文件
                    f.write(wav_data)
                return self.tmp
            else:
                return AudioSegment.from_file(io.BytesIO(wav_data))    
        else:
            raise 'TTS error, Please ask 卢家乐'


class TTSTalker_API():
    def __init__(self) -> None:
        self.origin_talker = TTSTalker()
        self.xiaoyuan_talker = TTSTalker1()
        self.another_talker = TTSTalker2()

    def test(self, text, talker=0, rvc=0, return_file=False):
        print(f'Begin TTS, text:{text}, talker:{int(talker)}, rvc:{int(rvc)}, return_file:{return_file}')
        if talker==0:
            return self.xiaoyuan_talker.test(text,rvc=rvc,return_file=return_file)
        elif talker==1:
            return self.origin_talker.test(text)
        else:
            return self.another_talker.test(text, int(talker), rvc=rvc, return_file=return_file)

if __name__ == '__main__':
    import time     
    tts = TTSTalker_API()
    start = time.time()
    tts.test('"这个TTS到底快不快阿"') # 1.03s
    print('cost time : ',time.time()-start)