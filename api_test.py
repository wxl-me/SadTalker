import requests
import os


def ask_arm(out_file='return_video.mp4', userText=None): 
    url = "http://192.168.102.22:9907/genVideo"
    payload={"userText":userText}
    headers = {
    'Cookie': 'HttpsAddress=; PCName=; SERVER_ID=; SID=; UdpAddress=; id1=; id2='
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload,verify=False,timeout=60)
    except requests.exceptions.ConnectTimeout:
        return 'Connect_timeout'
    except requests.exceptions.ReadTimeout:#超时异常
        return 'Read_timeout'
    except:
        return 'Other_error'
    if response.status_code==200:
        with open(out_file,'wb') as f:
            f.write(response.content)
            return 'ok'
    return 'error'

def test(out_file='return_video.mp4',userText='你好啊，我是小元'):
    res = ask_arm(userText=userText)
    print(res)
    if res == 'ok':
        os.system('mplayer -fs ' + out_file)
print('0')