import pyaudio
import wave
import playsound
command = [
                'ffmpeg',
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
					"-rtmp_buffer", "100",
					'-acodec', 'aac',
					'-f', 'flv', #  flv rtsp
					'rtmp://127.0.0.1/live/2'
]
#pipe_audio = subprocess.Popen(command, stdin=subprocess.PIPE, shell=False)

command = [
			'ffmpeg',
			'-y',
			'-i', 'pipe:',
			'-vcodec',
			'h264'
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

start_audio()

