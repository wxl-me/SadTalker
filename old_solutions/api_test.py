import requests
import os,io
import time
import threading
import base64,json
from ffpyplayer.player import MediaPlayer
from sseclient import SSEClient
import cv2
from playsound import playsound
from pydub.playback import play
from pydub import AudioSegment
import re
url1 = 'http://106.14.125.228:50031/api/open/openchat' #测试版
url2 = 'http://36.140.15.200:8002/api/open/openchat' #正式版
url3 = 'http://36.140.15.200:8003/api/m/qa/chat' #正式版stream

idle = True
time_n = 0
last = time.time()
begin_play = False
stop_play = 0
video_cache = []
audio_cache = []

def get_sse_stream(text):
    word_point = 0
    has_jh = False
    has_1 = True
    out = []
    response = requests.post(url3, stream=True, json={"message_id":13, "text":text})
    pattern = r'，|。|、|；'
    n = 0
    for chunk in response.iter_lines(decode_unicode=True, delimiter='-----'):
        if chunk:
            result_list = re.split(pattern, chunk.replace('\n',''))
            word_len = len(result_list)
            if word_len==1 and not has_jh:
                if len(result_list[0])>9:
                    print('1',result_list[0][:10])
                    has_jh = True
                    word_point = 2
            if word_len==2 and has_1 and len(result_list[0])!=10:
                print('2',result_list[0][has_jh*10:])
                has_1 = False
                word_point = 3
            if word_len>2 and word_len>word_point:
                print(word_point,result_list[-2])
                word_point = word_len
            '''if not has_jh:
                if '。' in chunk:
                    has_jh = True
                else:
                    continue
            else:
                word_list = chunk.replace('\n','').split('。')
                max_len = len(word_list)
                if max_len>word_point:
                    print(word_list[-2])
                    word_point = max_len'''
        out = chunk
    print('chunk: ',out)
def PlayVideo(video_path):
    global begin_play, stop_play, time_n
    n = 0
    def player(video_path):
        video = cv2.VideoCapture(video_path)
        pl = MediaPlayer(video_path[:-4]+'.wav')
        while True:
            res, frame = video.read()
            if not res:
                print("End of video : ",n)
                return
            cv2.waitKey(1000//25)
            '''if cv2.waitKey(1000//25) & 0xFF == ord("q"):
                break'''
            cv2.imshow("Video", frame)   
    while True:
        if begin_play and n<=time_n:
            print('now play : ', n, ' pull : ', time_n)
            player(video_path=video_path + 'got_video_' + str(n) + '.mp4')
            n += 1
        else:
            time.sleep(0.05)
        if n>time_n and stop_play:
            stop_play = False
            time_n = 0
            begin_play = False
            break
def PlayVideo2(video_path):
    global begin_play, stop_play, time_n, video_cache, audio_cache
    n = 0
    def play_audio(audio_cache):
        global begin_play
        if begin_play:
            while len(audio_cache):
                to_play = audio_cache.pop(0)
                playsound(to_play)
                print('play ', to_play)
        else:
            time.sleep(0.05)
            print('no')
    
    while True:
        if begin_play and n<=time_n:
            if n==0:
                threading.Thread(target=play_audio,args=(audio_cache,)).start()
            while len(video_cache):
                cv2.waitKey(1000//25)
                cv2.imshow("Video", video_cache.pop(0)[1])   
            n += 1
        else:
            time.sleep(0.05)
        if n>time_n and stop_play:
            stop_play = False
            time_n = 0
            begin_play = False
            break
def test(userText='',gpt=True,play=False):
    global idle, time_n, last, begin_play, stop_play
    test = "http://192.168.102.22:9907/test"
    test_n = '2'
    response_text = userText
    start = time.time()
    def send_thread():
        try:
            response = requests.request("POST", test+'_send'+test_n, data={"userText":response_text}, verify=False, timeout=30)
        except:
            print('close send pipe')
    threading.Thread(target=send_thread).start()
    print('send text cost time: ',time.time()-start)
    if play:
        messages = SSEClient(test+test_n)
        dir_name = 'results/' + time.strftime("%Y_%m_%d_%H.%M.%S") + '/' 
        os.makedirs(dir_name)
        got_video = dir_name + 'got_video_' + str(time_n) + '.mp4'
        threading.Thread(target=PlayVideo2,args=(dir_name,)).start()
        idle = False
        last = time.time()
        for msg in messages:
            if msg.event == 'message':
                if msg.data == '':
                    break
                data = eval(msg.data)
                stream = base64.b64decode(eval(data['value']))
                audio =  base64.b64decode(eval(data['audio']))
                with open(got_video,'wb') as f:
                    f.write(stream)
                '''   '''
                with open(got_video[:-4]+'.wav','wb') as f:
                    f.write(audio)
                length = AudioSegment.from_file(got_video[:-4]+'.wav').duration_seconds

                v = cv2.VideoCapture(got_video)
                for i in range(int(v.get(cv2.CAP_PROP_FRAME_COUNT))):
                    if i>length*25+1:
                        break
                    video_cache.append(v.read())
                
                audio_cache.append(got_video[:-4]+'.wav')#AudioSegment.from_file(io.BytesIO(audio)))#from_raw(audio,sample_width=4,frame_rate=16000,frame_width=4,channels=1))
                '''   '''
                begin_play = True
                time_n += 1
                got_video =  dir_name + 'got_video_' + str(time_n) + '.mp4'   
                print('time :',time_n,' push',' cost :',time.time()-last) 
                last = time.time()
        time_n -= 1     
        stop_play = True
        print('pull over')
        last = time.time()
        idle = True

test('简单介绍读书好处',gpt=False,play=True)

#get_sse_stream('你会干什么')
'''import librosa
from pydub import AudioSegment
import numpy as np
file = 'examples/driven_audio/deyu.wav'
a = librosa.core.load(file,sr=16000)[0]
b = AudioSegment.from_wav(file) 

c = b.set_frame_rate(16000)
c = c.set_channels(1)
d = np.array(c.get_array_of_samples())/2**31'''

print('ok')
