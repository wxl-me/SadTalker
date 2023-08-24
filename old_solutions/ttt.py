import cv2,os
import numpy as np
from ffpyplayer.player import MediaPlayer
import pyautogui, time, threading
begin_play,stop_play = False,999

def PlayVideo(video_path):
    global begin_play,stop_play
    n = 0
    def player(video_path):
        video = cv2.VideoCapture(video_path)
        MediaPlayer(video_path)
        while True:
            res, frame = video.read()
            if not res:
                print("End of video")
                return

            if cv2.waitKey(1000//25) & 0xFF == ord("q"):
                break
            cv2.imshow("Video", frame)   
    while True:
        if begin_play and n<stop_play:
            player(video_path=video_path + 'got_video_' + str(n) + '.mp4')
            n += 1
        else:
            time.sleep(0.1)
        if n>=stop_play:
            break

'''dir_name = 'results/' + str(time.time()).split('.')[0] + '/'
os.makedirs(dir_name)
n = 0
got_video = dir_name + '_0'
threading.Thread(target=PlayVideo,args=(dir_name,)).start()
while n<20:
    os.system('cp got_video.mp4 '+dir_name + 'got_video_' + str(n) + '.mp4')
    begin_play = True
    n += 1
    print('play ', n)
stop_play = n

print('over')'''

import os
li = os.listdir('.')
with open('daochu.txt','w+') as f:
    for i in li:
        if '.' not in i:
            f.writelines(i+'/\n')
        else:
            f.writelines(i+'\n')
print()