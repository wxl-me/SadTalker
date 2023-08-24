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

def PlayVideo2(video_path):
    global begin_play, stop_play, time_n, video_cache
    while True:
        if begin_play and len(video_cache):
            while len(video_cache):
                cv2.waitKey(1000//25)
                cv2.imshow('Video', video_cache.pop(0)[1])   
        else:
            time.sleep(0.05)
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
    global begin_play, stop_play, time_n, video_cache,thread_n
    n = 0
    while True:
        if begin_play and n<time_n:
            '''if n==0:
                multiprocessing.Process(target=video_process,args=(video_cache,))'''
            while len(audio_cache):
                to_play = audio_cache.pop(0)
                playsound(to_play)
                print('play ', to_play)
                n += 1
        else:
            time.sleep(0.1)
            #print('no')
        if n>=time_n and stop_play>0:
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
def test(userText='',gpt=True,play=False,thread=0):
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
        #threading.Thread(target=PlayVideo2,args=(dir_name,)).start()
        threading.Thread(target=play_audio,args=(audio_cache,thread)).start()
        idle = False
        last = time.time()
        for msg in messages:
            if msg.event == 'message':
                if msg.data == '':
                    break
                data = eval(msg.data)
                stream = base64.b64decode(eval(data['value']))
                audio =  base64.b64decode(eval(data['audio']))
                text = base64.b64decode(eval(data['text'])).decode()
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
def thread(ttt,thread):
    test(ttt,gpt=False,play=True,thread=thread)
threading.Thread(target=PlayVideo2,args=('v',)).start()
while True:
    thread_n = 1
    threading.Thread(target=thread,args=('你是谁',1)).start()
    input()
    thread_n = 2
    threading.Thread(target=thread,args=('你会干什么',2)).start()
    input()
    thread_n = 3
    threading.Thread(target=thread,args=('介绍一下深圳',3)).start()
    input()