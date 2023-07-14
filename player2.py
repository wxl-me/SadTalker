import cv2
import numpy as np
from ffpyplayer.player import MediaPlayer
import pyautogui, time, threading, os, subprocess
video_path = "/home/aimall/Downloads/WDA_AlexandriaOcasioCortez_000.mp4"

command = ["ffplay",
            video_path
        ]
pipe = subprocess.Popen(command, stdin=subprocess.PIPE, shell=False)
while True:
    if cv2.waitKey(0) & 0xff == ord('0'):
        pipe.stdin.write('q')
        