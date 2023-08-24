import torch
from time import  strftime
import os, sys, time
from argparse import ArgumentParser
import platform
from src.utils.preprocess import CropAndExtract
from src.test_audio2coeff import Audio2Coeff  
from src.facerender.pirender_animate import AnimateFromCoeff_PIRender
from src.generate_batch import get_data
from src.generate_facerender_batch import get_facerender_data
from src.utils.init_path import init_path
import time,json,base64
import  threading
from flask import Flask, jsonify, request, make_response, send_from_directory, Response
from src.utils.text2speech import TTSTalker_API
from gevent import pywsgi
from pydub import AudioSegment
import requests, re

class GenVideoApi(object):
    def __init__(self, args):
        self.duration = 0
        self.now_duration = 0
        self.wav_tts = []
        ''' TTS产生的语音队列 '''
        self.wav_tts_ok = False
        ''' TTS完毕的标志位 '''
        self.time = 0
        self.cache = [] 
        ''' 合成的视频队列 '''
        self.render_ok = False
        ''' 视频合成完毕的标志位 '''
        self.idle, self.time_n, self.last = True, time.time(), time.time()
        self.render_error = False
        self.tts = TTSTalker_API()
        self.app = Flask("__main__")  # web framework
        pic_path = args.source_image
        audio_path = args.driven_audio
        save_dir = os.path.join(args.result_dir, strftime("%Y_%m_%d_%H.%M.%S"))
        os.makedirs(save_dir, exist_ok=True)
        pose_style = args.pose_style
        device = args.device
        batch_size = args.batch_size
        input_yaw_list = args.input_yaw
        input_pitch_list = args.input_pitch
        input_roll_list = args.input_roll
        ref_eyeblink = args.ref_eyeblink
        ref_pose = args.ref_pose

        current_root_path = os.path.split(sys.argv[0])[0]
        sadtalker_paths = init_path(args.checkpoint_dir, os.path.join(current_root_path, 'src/config'), args.size, args.old_version, args.preprocess)

        #init model
        self.preprocess_model = CropAndExtract(sadtalker_paths, device)
        self.audio_to_coeff = Audio2Coeff(sadtalker_paths,  device)
        self.animate_from_coeff = AnimateFromCoeff_PIRender(sadtalker_paths, device)

        #crop image and extract 3dmm from image
        first_frame_dir = os.path.join(save_dir, 'first_frame_dir')
        os.makedirs(first_frame_dir, exist_ok=True)
        print('3DMM Extraction for source image')
        self.first_coeff_path, crop_pic_path, crop_info =  self.preprocess_model.generate(pic_path, first_frame_dir, args.preprocess,\
                                                                                source_image_flag=True, pic_size=args.size)
        if self.first_coeff_path is None:
            print("Can't get the coeffs of the input")
            return
        
        if ref_eyeblink is not None:
            ref_eyeblink_videoname = os.path.splitext(os.path.split(ref_eyeblink)[-1])[0]
            ref_eyeblink_frame_dir = os.path.join(save_dir, ref_eyeblink_videoname)
            os.makedirs(ref_eyeblink_frame_dir, exist_ok=True)
            print('3DMM Extraction for the reference video providing eye blinking')
            ref_eyeblink_coeff_path, _, _ =  self.preprocess_model.generate(ref_eyeblink, ref_eyeblink_frame_dir, args.preprocess, source_image_flag=False)
        else:
            ref_eyeblink_coeff_path=None

        if ref_pose is not None:
            if ref_pose == ref_eyeblink: 
                ref_pose_coeff_path = ref_eyeblink_coeff_path
            else:
                ref_pose_videoname = os.path.splitext(os.path.split(ref_pose)[-1])[0]
                ref_pose_frame_dir = os.path.join(save_dir, ref_pose_videoname)
                os.makedirs(ref_pose_frame_dir, exist_ok=True)
                print('3DMM Extraction for the reference video providing pose')
                ref_pose_coeff_path, _, _ =  self.preprocess_model.generate(ref_pose, ref_pose_frame_dir, args.preprocess, source_image_flag=False)
        else:
            ref_pose_coeff_path=None

        print('prepare model ok!')

        @self.app.route("/test_send2",methods=["GET","POST"])
        def call_test_send2():
            self.wav_tts = []
            textmessage = request.form['userText']
            try:
                talker, rvc = request.form['talker'], request.form['rvc']
            except:
                talker, rvc = 0, 0
            self.time = time.time()
            print('get question : ', textmessage)

            def thread_gpt_tts(self:GenVideoApi, text, talker=0, rvc=0):
                ''' GPT->TTS->语音\n
                    从GPT上流式获取答案，并按句发送到TTS生成语音，将生成的语音放入self.wav_tts队列中。 
                '''
                url = 'http://36.140.15.200:8003/api/m/qa/chat' #正式版stream
                word_point = 0
                has_fh = False
                has_10 = False
                has_10_time = 0
                response = requests.post(url, stream=True, json={"message_id":13, "text":text})   
                voice_time = 0
                last = time.time()
                pos = 0
                #pattern = re.
                for chunk in response.iter_lines(decode_unicode=True, delimiter='-----'):
                    if chunk:
                        if 'err_code' in chunk:
                            print(chunk)
                            break
                        if not has_fh and not has_10:
                            if '。' in chunk or '，' in chunk or '：' in chunk or '！' in chunk or '？' in chunk or '；' in chunk: 
                                has_fh = True
                        else:
                            word_list = re.split('，|。|：|！|？|；', chunk.replace('\n',''))
                            max_len = len(word_list)
                            if max_len>word_point:
                                #print('time : ', word_point, 'word to tts : ', word_list[-2])
                                textmessage = word_list[-2]
                                word_point = max_len
                                part_audio = self.tts.test(textmessage, talker, rvc) #AudioSegment.from_file(self.tts.test(textmessage))
                                self.wav_tts.append((part_audio,textmessage))
                                voice_time += 1
                                if self.render_error:
                                    self.render_error = False
                                    print('render error, so gpt and tts stop')
                                    return

                self.wav_tts_ok = True
                print('tts cost time: ',time.time()-last, 'voice time is : ', voice_time)

            def thread_render(self:GenVideoApi):
                ''' 语音->视频\n
                    从self.wav_tts队列中获取语音段，并将语音段送入视频合成模型，生成视频并放入self.cache队列。 
                '''
                n = 1
                last = time.time()
                while len(self.wav_tts)==0:
                    if time.time()-last>15:
                        print('timeout error')
                        self.render_error = True
                        return 
                    else:
                        time.sleep(0.05)
                while len(self.wav_tts)!=0 or not self.wav_tts_ok: 
                    if len(self.wav_tts)==0:
                        time.sleep(0.05)
                        continue
                    segment, text = self.wav_tts.pop(0)
                    '''segment.export('./results/tmp.wav',format='wav') 
                    segment_path = './results/tmp.wav' '''
                    batch = get_data(self.first_coeff_path, segment, device, ref_eyeblink_coeff_path, still=args.still)
                    coeff_path = self.audio_to_coeff.generate(batch, save_dir, pose_style, ref_pose_coeff_path)
                    #coeff2video
                    data = get_facerender_data(coeff_path, crop_pic_path, self.first_coeff_path, segment, 
                                                batch_size, input_yaw_list, input_pitch_list, input_roll_list,
                                                expression_scale=args.expression_scale, still_mode=args.still, preprocess=args.preprocess, size=args.size, facemodel=args.facerender)
                    result, video, audio = self.animate_from_coeff.generate(data, save_dir, pic_path, crop_info, \
                                                enhancer=args.enhancer, background_enhancer=args.background_enhancer, preprocess=args.preprocess, img_size=args.size)
                    with open(result, 'rb') as f:
                        self.cache.append('data:'+json.dumps({'value': str(base64.b64encode(f.read())), 
                                                              'audio': str(base64.b64encode(audio.export(format='wav').read())),
                                                              'text': str(base64.b64encode(text.encode())),
                                                              })+'\n\n')
                    print('render time : ', n, 'word : ',text, ' last tts: ', len(self.wav_tts))
                    n += 1
                self.wav_tts, self.wav_tts_ok, self.render_ok = [], False, True
                print('render over')

            threading.Thread(target=thread_gpt_tts,args=(self, textmessage, int(talker), int(rvc))).start()
            threading.Thread(target=thread_render,args=(self,)).start()
            return jsonify('ok')

        @self.app.route("/test2",methods=["GET","POST"])
        def call_test2():
            ''' 将self.cache队列中的视频段发送到客户端\n
            '''
            print('remain data : ', len(self.cache), 'clean up cache')
            self.cache, self.render_ok = [], False
            def eventStream(self:GenVideoApi):
                last = time.time()
                while len(self.cache) != 0 or not self.render_ok:
                    if len(self.cache)==0:
                        time.sleep(0.05)
                    else:
                        yield self.cache.pop(0)

                self.render_ok = False
                self.cache = []
                print('push over')

            response = Response(eventStream(self), mimetype="text/event-stream")
            response.headers.add('Cache-Control', "no-store, no-cache, must-revalidate, max-age=0")
            response.headers.add('X-Accel-Buffering', 'no')
            return response
        

if __name__ == '__main__':

    parser = ArgumentParser()  
    parser.add_argument("--driven_audio", default='./examples/driven_audio/bus_chinese.wav', help="path to driven audio")
    parser.add_argument("--source_image", default='./examples/source_image/abm2.png', help="path to source image")
    parser.add_argument("--ref_eyeblink", default=None, help="path to reference video providing eye blinking")
    parser.add_argument("--ref_pose", default=None, help="path to reference video providing pose")
    parser.add_argument("--checkpoint_dir", default='./checkpoints', help="path to output")
    parser.add_argument("--result_dir", default='./results', help="path to output")
    parser.add_argument("--pose_style", type=int, default=1,  help="input pose style from [0, 46)")
    parser.add_argument("--batch_size", type=int, default=25,  help="the batch size of facerender")
    parser.add_argument("--size", type=int, default=256,  help="the image size of the facerender")
    parser.add_argument("--expression_scale", type=float, default=0.7,  help="the batch size of facerender")
    parser.add_argument('--input_yaw', nargs='+', type=int, default=None, help="the input yaw degree of the user ")
    parser.add_argument('--input_pitch', nargs='+', type=int, default=None, help="the input pitch degree of the user")
    parser.add_argument('--input_roll', nargs='+', type=int, default=None, help="the input roll degree of the user")
    parser.add_argument('--enhancer',  type=str, default=None, help="Face enhancer, [gfpgan, RestoreFormer]")
    parser.add_argument('--background_enhancer',  type=str, default=None, help="background enhancer, [realesrgan]")
    parser.add_argument("--cpu", dest="cpu", action="store_true") 
    parser.add_argument("--face3dvis", action="store_true", help="generate 3d face and 3d landmarks") 
    parser.add_argument("--still", action="store_true", help="can crop back to the original videos for the full body aniamtion") 
    parser.add_argument("--preprocess", default='crop', choices=['crop', 'extcrop', 'resize', 'full', 'extfull'], help="how to preprocess the images" ) 
    parser.add_argument("--verbose",action="store_true", help="saving the intermedia output or not" ) 
    parser.add_argument("--old_version",action="store_true", help="use the pth other than safetensor version" ) 
    parser.add_argument("--facerender", default='pirender', choices=['pirender', '']) 
    

    # net structure and parameters
    parser.add_argument('--net_recon', type=str, default='resnet50', choices=['resnet18', 'resnet34', 'resnet50'], help='useless')
    parser.add_argument('--init_path', type=str, default=None, help='Useless')
    parser.add_argument('--use_last_fc',default=False, help='zero initialize the last fc')
    parser.add_argument('--bfm_folder', type=str, default='./checkpoints/BFM_Fitting/')
    parser.add_argument('--bfm_model', type=str, default='BFM_model_front.mat', help='bfm model')

    # default renderer parameters
    parser.add_argument('--focal', type=float, default=1015.)
    parser.add_argument('--center', type=float, default=112.)
    parser.add_argument('--camera_d', type=float, default=10.)
    parser.add_argument('--z_near', type=float, default=5.)
    parser.add_argument('--z_far', type=float, default=15.)

    args = parser.parse_args()

    if torch.cuda.is_available() and not args.cpu:
        args.device = "cuda"
    elif platform.system() == 'Darwin' and args.facerender == 'pirender': # macos 
        args.device = "mps"
    else:
        args.device = "cpu"
    #args.still = True
    if 1:
        server = GenVideoApi(args)
        server.app.run(host='0.0.0.0', port=9907)
    else:
        api = GenVideoApi(args)
        server = pywsgi.WSGIServer(('0.0.0.0', 9907), api.app)
        server.serve_forever()
