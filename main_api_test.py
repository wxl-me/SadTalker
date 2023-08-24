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
import multiprocessing
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
thread_n = 0
voice_begin = False
video_num = []
def PlayVideo2(video_path):
    '''视频播放函数
    播放video_cache队列的视频帧文件
    '''
    global begin_play, stop_play, time_n, video_cache,voice_begin
    while True:
        if begin_play and voice_begin and len(video_cache):
            while len(video_cache):
                cv2.waitKey(1000//25)
                cv2.imshow('Video', video_cache.pop(0)[1])   
        else:
            time.sleep(0.1)
        if stop_play>0:
            if stop_play>1:
                stop_play = 0
                begin_play = False
                time_n = 0
            else:
                stop_play += 1 
            print('video play over -----------------------')
            #return
    #cv2.destroyWindow("Video")
def video_process(video_cache):
    while len(video_cache):
        cv2.waitKey(1000//25)
        cv2.imshow('video_path', video_cache.pop(0)[1])   
        
def play_audio(audio_cache,thread):
    '''音频播放函数
    播放audio_cache队列的音频文件
    '''
    global begin_play, stop_play, time_n, video_cache,thread_n,voice_begin
    n = 0
    while True:
        if begin_play and n<=time_n:
            '''if n==0:
                multiprocessing.Process(target=video_process,args=(video_cache,))'''
            while len(audio_cache):
                to_play = audio_cache.pop(0)
                voice_begin = True
                playsound(to_play)
                print('play ', to_play)
                n += 1
        else:
            time.sleep(0.1)
            #print('no')
        if n>time_n and stop_play>0:
            if stop_play>1:
                stop_play = 0
                begin_play = False
                time_n = 0
            else:
                stop_play += 1
            print('audio play over -----------------------')
            return
        if thread!=thread_n:
            print('audio break: ',thread, ' : ', thread_n)
            return
def test(userText='',gpt=True,play=False,thread=0,talker=0,rvc=0):
    '''    
    '''
    global idle, time_n, last, begin_play, stop_play
    test = "http://192.168.102.22:9907/test"
    test_n = '2'
    response_text = userText
    start = time.time()
    def send_thread(): # 首先发送问题文本到服务器
        try:
            response = requests.request("POST", test+'_send'+test_n, data={"userText":response_text,"talker":talker,"rvc":rvc}, verify=False, timeout=30)
        except:
            print('close send pipe')
    threading.Thread(target=send_thread).start() # 启动发送问题线程
    print('send text cost time: ',time.time()-start)
    if play:
        messages = SSEClient(test+test_n) # 开启流式接受数据
        dir_name = 'results/' + time.strftime("%Y_%m_%d_%H.%M.%S") + '/' 
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        got_video = dir_name + 'got_video_' + str(time_n) + '.mp4'
        #threading.Thread(target=PlayVideo2,args=(dir_name,)).start()
        threading.Thread(target=play_audio,args=(audio_cache,thread)).start()
        idle = False
        last = time.time()
        for msg in messages: # 查看流式接受的内容
            if msg.event == 'message':
                if msg.data == '':
                    break
                data = json.loads(msg.data) # 此为接受的数据，经过base64转码，需要进行解码
                stream = base64.b64decode(eval(data['value'])) # 视频帧
                audio =  base64.b64decode(eval(data['audio'])) # 音频
                text = base64.b64decode(eval(data['text'])).decode() # 返回的回答文本
                with open(got_video,'wb') as f:
                    f.write(stream)
                '''   '''
                with open(got_video[:-4]+'.wav','wb') as f:
                    f.write(audio)
                length = AudioSegment.from_file(got_video[:-4]+'.wav').duration_seconds # 音频的时间长度

                v = cv2.VideoCapture(got_video) 
                for i in range(int(v.get(cv2.CAP_PROP_FRAME_COUNT))):
                    if i>=length*25: # 视频最后几帧可能是静止的，为保持音视频同步，删除后续帧。
                        break
                    video_cache.append(v.read())
                v.set(cv2.CAP_PROP_POS_FRAMES, v.get(cv2.CAP_PROP_FRAME_COUNT) - 1) # 定位到最后一帧
                video_cache.append(v.read()) # 补充最后一帧到视频帧队列中，目的是防止动作突然变化(可能并不有效)
                video_num.append(i)
                audio_cache.append(got_video[:-4]+'.wav')#AudioSegment.from_file(io.BytesIO(audio)))#from_raw(audio,sample_width=4,frame_rate=16000,frame_width=4,channels=1))
                '''   '''
                begin_play = True
                time_n += 1
                got_video =  dir_name + 'got_video_' + str(time_n) + '.mp4'   
                print('time :', time_n, ' pull', ' text : ', text, ' cost :', time.time()-last) 
                last = time.time()
        time_n -= 1     
        stop_play = 1
        print('pull over')
        last = time.time()
        idle = True

#test('你是谁',gpt=False,play=True)

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
def thread(ttt,thread,talker,rvc):
    test(ttt,gpt=False,play=True,thread=thread,talker=talker,rvc=rvc)
def lau():
    global thread_n
    threading.Thread(target=PlayVideo2,args=('v',)).start()
    while True:
        input_ = input().split()
        try:
            i = int(input_[0])
        except:
            print('please input number')
            continue
        try:
            talker = input_[1]
        except:
            talker = 0
        try:
            rvc = input_[2]
        except:
            rvc = 0
        print(f'task:{i}, talker:{talker}, rvc:{rvc}')
        thread_n = i
        if i==1:
            threading.Thread(target=thread,args=('你好',i,talker,rvc)).start()
        elif i==2:
            threading.Thread(target=thread,args=('你会干什么',i,talker,rvc)).start()
        elif i==3:
            threading.Thread(target=thread,args=('介绍一下深圳',i,talker,rvc)).start()
        else:
            print('invalid number')

lau()