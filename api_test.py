import requests
import os
import time
import threading
import base64,subprocess,json
from ffpyplayer.player import MediaPlayer
from sseclient import SSEClient
import cv2
import pyautogui
from pydub.playback import play
from pydub import AudioSegment
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
def get_gpt(text):#获取gpt返回的文本
    json = {"question":text} 
    json_stream = {"message_id":13, "text":text}
    res = requests.get(url=url3, json=json_stream)
    
    return res
def get_sse_stream(text):
    word_point = 0
    has_jh = False
    out = []
    response = requests.post(url3, stream=True, json={"message_id":13, "text":text})
    for chunk in response.iter_lines(decode_unicode=True, delimiter='-----'):
        if chunk:
            if not has_jh:
                if '。' in chunk:
                    has_jh = True
                else:
                    continue
            else:
                word_list = chunk.replace('\n','').split('。')
                max_len = len(word_list)
                if max_len>word_point:
                    print(word_list[-2])
                    word_point = max_len
            
def get_sse_stream1(text):
    messages = SSEClient(url3) 
    for msg in messages:
        if msg.event == 'message':
            if msg.data == '':
                break
            print(msg.data)

def ask_gpt(userText, timeout=80, play=True, full_screen=True): #获取gpt后用视频播放
    json = {"question":userText} 
    try:
        start = time.time()
        response = requests.post(url=url2, json=json, timeout=timeout)
        if response.status_code==200:
            response_text = response.content.decode().split('"result":"')[-1].split('"}')[0]
            print('您的提问是: '+userText)
            print('GPT的回答是: ' +response_text)
            print('GPT生成时间: '+str(time.time()-start)+' 秒')
            start = time.time()
            res = genVideo(out_file="./return_video.mp4",userText=response_text)
            print('视频生成时间: '+str(time.time()-start)+' 秒')
            if res=='ok':
                if full_screen:
                    os.system('mplayer -fs ' + "./return_video.mp4")
                else:
                    os.system('mplayer ' + "./return_video.mp4")
            else:
                print('Generate Video Error '+res)
            return 'ok'+' :ask_gpt'
        else:
            return 'Post Error Code: '+str(response.status_code)+' :ask_gpt'
    except requests.exceptions.ConnectTimeout:
        return 'Connect_timeout'+' :ask_gpt'
    except requests.exceptions.ReadTimeout:#超时异常
        return 'Read_timeout'+' :ask_gpt'
    except:
        return 'Other_error'+' :ask_gpt'    

def genVideo(out_file='return_video.mp4', userText=None): 
        '''文本生成视频\n
        Args:
            out_file: 保存的路径和名称\n
            userText: 待转换的文本\n
        Returns:
            生成状态: Connect_timeout / Read_timeout / Other_error / ok / error
        '''
        genVideoUrl = "http://192.168.102.22:9907/genVideoStream"
        payload={"userText":userText}
        headers = {'Cookie': 'HttpsAddress=; PCName=; SERVER_ID=; SID=; UdpAddress=; id1=; id2='}
        try:
            response = requests.request("GET", genVideoUrl, headers=headers, data=payload, verify=False, timeout=60)
        except requests.exceptions.ConnectTimeout:
            return 'Connect_timeout'+' :genVideo'
        except requests.exceptions.ReadTimeout:#超时异常
            return 'Read_timeout'+' :genVideo'
        except:
            return 'Other_error'+' :genVideo'
        if response.status_code==200:
            with open(out_file,'wb') as f:
                f.write(response.content)
                return 'ok'
        return 'error'+' :genVideo'   

def getVideoPart(userText=''):
    start = time.time()
    response = requests.post(url=url2, json={"question":userText} , timeout=30)
    if response.status_code==200:
        response_text = response.content.decode().split('"result":"')[-1].split('"}')[0]
        print('您的提问是: '+userText)
        print('GPT的回答是: ' +response_text)
        print('GPT生成时间: '+str(time.time()-start)+' 秒')
    else:
        print('GPT Error Code: '+response.status_code)
    
    genVideoUrl = "http://192.168.102.22:9907/genVideoStream"
    headers = {'Cookie': 'HttpsAddress=; PCName=; SERVER_ID=; SID=; UdpAddress=; id1=; id2='}
    def thread_post(question):
        print('Start send text to video')
        response = requests.request("GET", genVideoUrl, headers=headers, data={"userText":question}, verify=False, timeout=90)
    threading.Thread(target=thread_post,args=(response_text,)).start() # 发起视频生成请求

    getVideoDuration = "http://192.168.102.22:9907/getVideoDuration"
    duration = requests.request("GET", getVideoDuration, headers=headers, verify=False, timeout=30)
    if duration==0:
        print('API failed to get tts result')
        return 'API failed to get tts result'
    print('Get GPT TTS time :'+duration.content["duration"])

    getVideo = "http://192.168.102.22:9907/getVideo"
    for n in range(int(eval(duration.content)["duration"])+1):
        response = requests.request("GET", getVideo, headers=headers, verify=False, timeout=30)
        if response.status_code==200:
            with open('return_video'+str(n)+'.mp4','wb') as f:
                f.write(response.content)
            os.system('mplayer '+'return_video.mp4')

def continuous():
    global idle,time_n,last
    last=time.time()
    while True:
        if idle:
            while time.time()-last<0.9:
                time.sleep(0.1)
            if not idle:
                continue
            os.system('ffmpeg -i ' + 'idle.mp4' + ' -acodec aac -ar 44100 -vcodec h264 -r 25 -f flv rtmp://127.0.0.1/live/1 -loglevel quiet')       
            time_n += 1
            print('time :',time_n,' idle',' cost :',time.time()-last)
            last = time.time()
def PlayVideo(video_path):
    global begin_play, stop_play, time_n
    n = 0
    def player(video_path):
        video = cv2.VideoCapture(video_path)
        pl = MediaPlayer(video_path)
        while True:
            res, frame = video.read()
            if not res:
                print("End of video : ",n)
                return

            if cv2.waitKey(1000//25) & 0xFF == ord("q"):
                break
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
        while len(audio_cache):
            to_play = audio_cache.pop(0)
            play(to_play)
    while True:
        if begin_play and n<=time_n:
            threading.Thread(target=play_audio,args=(audio_cache,)).start()
            while len(video_cache):
                if cv2.waitKey(1000//25) & 0xFF == ord("q"):
                    break
                cv2.imshow("Video", video_cache.pop(0)[1])   
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
    start = time.time()
    if gpt:
        start = time.time()
        response = requests.post(url=url2, json={"question":userText} , timeout=60)
        if response.status_code==200:
            response_text = response.content.decode().split('"result":"')[-1].split('"}')[0]
            print('您的提问是: '+userText)
            print('GPT的回答是: ' +response_text)
            print('GPT生成时间: '+str(time.time()-start)+' 秒')
        else:
            print('GPT Error Code: '+response.status_code)
    else:
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
                stream = base64.b64decode(eval(eval(msg.data)['value']))
                with open(got_video,'wb') as f:
                    f.write(stream)
                '''   '''
                v = cv2.VideoCapture(got_video)
                for _ in range(int(v.get(cv2.CAP_PROP_FRAME_COUNT))):
                    video_cache.append(v.read())
                audio_cache.append(AudioSegment.from_file(got_video))
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

'''response = get_gpt('介绍一下深圳')
print(response.content.decode().split('"result":"')[-1].split('"}')[0])#'''

#response = requests.get(url3, stream=True, json={"message_id":13, "text":'你是谁'}) 
#get_sse_stream('介绍一下深圳')

'''response = getVideoPart('你认识openai么')
print(response)
print('0')'''

test('介绍一下你会干什么',gpt=False,play=True)
'''time.sleep(5)
time.sleep(5)'''

#'''
'''response = get_gpt('你好阿')
print(response.status_code)
print(response.content)'''