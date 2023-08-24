import cv2
import numpy as np
from ffpyplayer.player import MediaPlayer
import pyautogui, time, threading
video_path = "/home/aimall/Downloads/imageitosinger1-0-100 (1).mp4"

def PlayVideo(video_path):
    video = cv2.VideoCapture(video_path)
    player = MediaPlayer(video_path)
    while True:
        res, frame = video.read()
        #audio_frame, val = player.get_frame()
        if not res:
            def thread():
                time.sleep(1)
                pyautogui.write('0')
            threading.Thread(target=thread).start()
            cv2.waitKey(0)
            print("End of video")
            return

        if cv2.waitKey(1000//25) & 0xFF == ord("q"):
            break
        cv2.imshow("Video", frame)
        '''if val != 'eof' and audio_frame is not None:
            # audio
            img, t = audio_frame'''
            # print(img, t)
        
    #video.release()
    #cv2.destroyAllWindows()

PlayVideo(video_path)
PlayVideo(video_path)

# way2
'''import cv2
import numpy as np
from ffpyplayer.player import MediaPlayer
import pyautogui, time, threading, os, subprocess
video_path = "/home/aimall/Downloads/WDA_AlexandriaOcasioCortez_000.mp4"

command = ["ffplay",
            video_path]
pipe = subprocess.Popen(command, stdin=subprocess.PIPE, shell=False)
while True:
    if cv2.waitKey(0) & 0xff == ord('0'):
        pipe.stdin.write('q')'''