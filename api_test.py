import requests
import os
import time
import threading
import base64,subprocess
url1 = 'http://106.14.125.228:50031/api/open/openchat' #测试版
url2 = 'http://36.140.15.200:8002/api/open/openchat' #正式版
url3 = 'http://36.140.15.200:8002/api/m/qa/chat' #正式版stream

def get_gpt(text):#获取gpt返回的文本
    json = {"question":text} 
    json_stream = {"message_id":13, "text":text}
    res = requests.post(url=url3, json=json_stream)
    return res

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
    
def test():
    from sseclient import SSEClient
    test = "http://192.168.102.22:9907/test"
    command = [
			'ffmpeg',
			'-y',
			'-i', '-',
			'-vcodec',
			'h264'
            '-acodec',
            '-ar',
            '44100',
            '-r',
            '25',
			'-f', 'flv',
			'rtmp://127.0.0.1/live/1'
    ]
    #pipe_all = subprocess.Popen(command, stdin=subprocess.PIPE, shell=False)
    messages = SSEClient(test)
    time_n = 0
    got_video = 'got_video.mp4'
    for msg in messages:
        if msg.event == 'message':
            if msg.data == '':
                print('over')
                break
            stream = base64.b64decode(eval(eval(msg.data)['value']))
            with open('got_video.mp4','wb') as f:
                f.write(stream)
            #pipe_all.stdin.write('got_video.mp4')
            os.system('ffmpeg -i ' + got_video + ' -acodec aac -ar 44100 -vcodec h264 -r 25 -f flv rtmp://127.0.0.1/live/1')
            #os.system('mplayer '+got_video)
            print(time_n)
            time_n += 1
    #3548230
    #12740011
'''response = get_gpt('介绍一下深圳')
print(response.content.decode().split('"result":"')[-1].split('"}')[0])#'''

'''response = getVideoPart('你认识openai么')
print(response)
print('0')'''

test()
'''response = get_gpt('你好阿')
print(response.status_code)
print(response.content)'''