import pyaudio
import wave
import playsound
import subprocess
import time 
from pydub import AudioSegment 
import librosa
import numpy as np
import os
from moviepy.editor import *
command = [ 'ffmpeg',
			'-y',
			'-f',
			'rawvideo',
			'-vcodec',
			'rawvideo',
			'-pix_fmt',
			'bgr24',
			'-s', "{}x{}".format(256, 256),  # 图片分辨率
			#'-r', str(25.0),  # 视频帧率
			'-i', 'pipe:',
			'-c:v', 'libx264',
			#'-pix_fmt', 'yuv420p',
			'-preset', 'ultrafast',
			'-f', 'flv',
			'rtmp://127.0.0.1/live/1'
    ]
#pipe_video = subprocess.Popen(command, stdin=subprocess.PIPE, shell=False)

command = ['ffmpeg', # linux不用指定
			'-f', 's16le',
			'-y', '-vn',
			'-acodec','pcm_s16le',
			'-i', '-',
			'-ac', '1',
			'-ar', '44100',
			"-rtmp_buffer", "100",
			'-acodec', 'aac',
			'-f', 'flv', #  flv rtsp
			'rtmp://127.0.0.1/live/2'
]
#pipe_audio = subprocess.Popen(command, stdin=subprocess.PIPE, shell=False)

command = [
			'ffmpeg',
			'-i', '-',
			'-vcodec',
			'h264',
			'-acodec',
			'aac',
			'-ar',
			'44100',
			'-r',
			'25',
			'-f', 'flv',
			'rtmp://127.0.0.1/live/1'
]
#pipe_all = subprocess.Popen(command, stdin=subprocess.PIPE, shell=False)

def start_audio(time = 10,save_file="test.wav"):
	CHUNK = 4410
	FORMAT = pyaudio.paInt16
	CHANNELS = 2
	RATE = 44100
	RECORD_SECONDS = time  #需要录制的时间
	WAVE_OUTPUT_FILENAME = save_file	#保存的文件名

	p = pyaudio.PyAudio()	#初始化
	print("ON")

	stream = p.open(format=FORMAT,
	                channels=CHANNELS,
	                rate=RATE,
	                input=True,
		            frames_per_buffer=CHUNK,
					input_device_index=-1
						)#创建录音文件
	frames = []
	for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
		data = stream.read(CHUNK)
		frames.append(data) # 开始录音
    

	print("OFF")

	stream.stop_stream()
	stream.close()
	p.terminate()

	wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')	#保存
	wf.setnchannels(CHANNELS)
	wf.setsampwidth(p.get_sample_size(FORMAT))
	wf.setframerate(RATE)
	wf.writeframes(b''.join(frames))
	wf.close()

	playsound.playsound('./test.wav')

#start_audio()

#audio = AudioSegment.from_file('examples/driven_audio/bus_chinese.wav')
'''audio = librosa.load('examples/ttt.wav',sr=16000)
audio = (audio[0]*32767).astype(np.int16)
last = time.time() 
while 0:
	if time.time()-last>0.95:
		pipe_audio.stdin.write(audio.tosting())
		last = time.time()
		print('push')
	else:
		time.sleep(0.05)

part = int(16000/25)
n = len(audio)//part
pipe_audio.stdin.write(audio.tobytes())
for i in range(n-1):
	if time.time()-last>0.04:
		voice = audio[i*part:(i+1)*part]
		pipe_audio.stdin.write(voice.tobytes())
		last = time.time()
		print('push ', i)
	else:
		time.sleep(0.05)'''
command = [ 'ffmpeg',
			'-y',
			'-vcodec',
			'h264',
			'-acodec',
			'aac',
			'-r', str(25.0),  # 视频帧率

			'-i', 'pipe:',
			'-c:v', 'libx264',
			'-ac', '1',
			'-ar', '44100',
			'-f', 'flv',
			'rtmp://127.0.0.1/live/1'
    ]
pipe = subprocess.Popen(command, stdin=subprocess.PIPE, shell=False)
video = '/home/aimall/xiaolongwang/stable-diffusion-webui/extensions/SadTalker/results/2023_08_02_17.43.45/art_6##tmp.mp4'
video = VideoFileClip(video)
audio = video.audio
last = time.time() 
while 1:
	if time.time()-last>0.95:
		#os.system('ffmpeg -i ' + video + ' -acodec aac -ar 44100 -vcodec h264 -r 25 -f flv rtmp://127.0.0.1/live/1 -loglevel quiet')
		pipe.stdin.write() 
		last = time.time()
		print('push ',last)
	else:
		time.sleep(0.05)