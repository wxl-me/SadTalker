import torch
from time import  strftime
import os, sys, time
from argparse import ArgumentParser
import platform
from src.utils.preprocess import CropAndExtract
from src.test_audio2coeff import Audio2Coeff  
from src.facerender.animate import AnimateFromCoeff
from src.facerender.pirender_animate import AnimateFromCoeff_PIRender
from src.generate_batch import get_data
from src.generate_facerender_batch import get_facerender_data
from src.utils.init_path import init_path
import time,json,base64
import multiprocessing as mp
import pyaudio, wave, threading
from flask import Flask, jsonify, request, make_response, send_from_directory, Response
from src.utils.text2speech import TTSTalker_API
from gevent import pywsgi
from pydub import AudioSegment
from moviepy import editor

class GenVideoApi(object):
    def __init__(self, args):
        self.duration = 0
        self.now_duration = 0
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
        
        if args.facerender == 'facevid2vid':
            self.animate_from_coeff = AnimateFromCoeff(sadtalker_paths, device)
        elif args.facerender == 'pirender':
            self.animate_from_coeff = AnimateFromCoeff_PIRender(sadtalker_paths, device)
        else:
            raise(RuntimeError('Unknown model: {}'.format(args.facerender)))

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


        @self.app.route("/genVideo", methods=["POST"])
        def call_generate_video():
            begin_t = time.time()
            textmessage = request.form
            wav_tts = self.tts.test(textmessage['userText'])

            #pose_style = random.randint(0,45)
            #audio2ceoff
            batch = get_data(self.first_coeff_path, wav_tts, device, ref_eyeblink_coeff_path, still=args.still)
            coeff_path = self.audio_to_coeff.generate(batch, save_dir, pose_style, ref_pose_coeff_path)
            
            #coeff2video
            data = get_facerender_data(coeff_path, crop_pic_path, self.first_coeff_path, wav_tts, 
                                        batch_size, input_yaw_list, input_pitch_list, input_roll_list,
                                        expression_scale=args.expression_scale, still_mode=args.still, preprocess=args.preprocess, size=args.size, facemodel=args.facerender)
            
            result = self.animate_from_coeff.generate(data, save_dir, pic_path, crop_info, \
                                        enhancer=args.enhancer, background_enhancer=args.background_enhancer, preprocess=args.preprocess, img_size=args.size)
            
            #os.system('mplayer -fs ' + result)
            print('cost time : ', time.time()-begin_t)
            try:
                response = make_response(send_from_directory('', result, as_attachment=True))
                return response
            except Exception as e:
                return jsonify({"code": "异常", "message": "{}".format(e)})
            
        @self.app.route("/genVideoStream", methods=["GET"])
        def call_generate_video_stream():    
            textmessage = request.form
            wav_tts = self.tts.test(textmessage['userText'])
            audio = AudioSegment.from_file(wav_tts)
            self.duration = audio.duration_seconds # 单位为秒

            for t in range(int(self.duration)+1):
                self.now_duration = t
                segment = audio[t*1000:(t+1)*1000]
                segment.export('./results/tmp.wav',format='wav')
                segment_path = './results/tmp.wav'
                batch = get_data(self.first_coeff_path, segment_path, device, ref_eyeblink_coeff_path, still=args.still)
                coeff_path = self.audio_to_coeff.generate(batch, save_dir, pose_style, ref_pose_coeff_path)
                #coeff2video
                data = get_facerender_data(coeff_path, crop_pic_path, self.first_coeff_path, segment_path, 
                                            batch_size, input_yaw_list, input_pitch_list, input_roll_list,
                                            expression_scale=args.expression_scale, still_mode=args.still, preprocess=args.preprocess, size=args.size, facemodel=args.facerender)
                result = self.animate_from_coeff.generate(data, save_dir, pic_path, crop_info, \
                                            enhancer=args.enhancer, background_enhancer=args.background_enhancer, preprocess=args.preprocess, img_size=args.size)
                return jsonify({"path": result})    
                 
        @self.app.route("/getVideoDuration", methods=["GET"])
        def call_get_audio_duration():
            start = time.time()
            while self.duration==0:
                if time.time()-start>30:
                    return jsonify({"duration":0})
            return jsonify({"duration":self.duration})
        
        @self.app.route("/getVideo", methods=["GET"])
        def call_get_video():
            textmessage = request.form
            need_n = textmessage['n']
            start = time.time()
            while self.now_duration<need_n:
                if time.time()-start>10:
                    return jsonify({"error":"timeout"})
            video = 'return_video'+str(need_n)+'.mp4'
            try:
                response = make_response(send_from_directory('', video, as_attachment=True))
                return response
            except Exception as e:
                return jsonify({"error": "异常", "message": "{}".format(e)})
            
        @self.app.route("/test",methods=["GET","POST"])
        def call_test():
            #textmessage = request.form
            def eventStream(textmessage):
                wav_tts = self.tts.test(textmessage['userText'])
                audio = AudioSegment.from_file(wav_tts)  
                self.duration = audio.duration_seconds # 单位为秒              
                for t in range(int(self.duration)+1):
                    self.now_duration = t
                    segment = audio[t*1000:(t+1)*1000]
                    segment.export('./results/tmp.wav',format='wav')
                    segment_path = './results/tmp.wav'
                    batch = get_data(self.first_coeff_path, segment_path, device, ref_eyeblink_coeff_path, still=args.still)
                    coeff_path = self.audio_to_coeff.generate(batch, save_dir, pose_style, ref_pose_coeff_path)
                    #coeff2video
                    data = get_facerender_data(coeff_path, crop_pic_path, self.first_coeff_path, segment_path, 
                                                batch_size, input_yaw_list, input_pitch_list, input_roll_list,
                                                expression_scale=args.expression_scale, still_mode=args.still, preprocess=args.preprocess, size=args.size, facemodel=args.facerender)
                    result = self.animate_from_coeff.generate(data, save_dir, pic_path, crop_info, \
                                                enhancer=args.enhancer, background_enhancer=args.background_enhancer, preprocess=args.preprocess, img_size=args.size)
                    with open(result, 'rb') as f:
                        yield 'data:'+json.dumps({'value': str(base64.b64encode(f.read()))})+'\n\n'
            
            return Response(eventStream(textmessage={'userText':'我是一个人工智能语音助手，您可以提问我'}), mimetype="text/event-stream")

    #生成图像 <div id="component-8" class="block svelte-mppz8v" style="width: 256px; border-style: solid; overflow: hidden; background-color: rgb(193, 230, 198); border-color: rgba(0, 0, 0, 0.35);"><div class="wrap default svelte-j1gjts hide" style="position: absolute; padding: 0px; background-color: rgb(193, 230, 198);"></div> <div style="background-color: rgb(193, 230, 198); border-bottom-color: rgba(0, 0, 0, 0.35); border-right-color: rgba(0, 0, 0, 0.35);" class="svelte-1sohkj6 float"><span class="svelte-1sohkj6"><svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="feather feather-video"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg></span> 已生成视频</div> <div class="wrap svelte-1vnmhm4" style="opacity: 1; background-color: rgb(193, 230, 198);"><video src="http://192.168.102.22:7860/file=/tmp/gradio/ac955accc8f2622a4ba6ab86c59e7463ea2f213c/imageidlemode_2.0.mp4" preload="auto" class="svelte-1vnmhm4" style="opacity: 1; transition: all 0.2s ease 0s;"><track kind="captions" default=""></video> <div class="controls svelte-1vnmhm4" style="opacity: 0; transition: all 0.2s ease 0s;"><div class="inner svelte-1vnmhm4"><span class="icon svelte-1vnmhm4"><svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="feather feather-rotate-ccw"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg></span> <span class="time svelte-1vnmhm4">0:02 / 0:02</span> <progress value="1" class="svelte-1vnmhm4"></progress> <div class="icon svelte-1vnmhm4"><svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path></svg></div></div></div></div> <div class="download svelte-90pr3x" data-testid="download-div"><a href="http://192.168.102.22:7860/file=/tmp/gradio/ac955accc8f2622a4ba6ab86c59e7463ea2f213c/imageidlemode_2.0.mp4" download="imageidlemode_2.0.mp4"><button aria-label="Download" class="svelte-1p4r00v" style="background-color: rgb(193, 230, 198); border-color: rgba(0, 0, 0, 0.35);"><div class="svelte-1p4r00v"><svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 32 32"><path fill="currentColor" d="M26 24v4H6v-4H4v4a2 2 0 0 0 2 2h20a2 2 0 0 0 2-2v-4zm0-10l-1.41-1.41L17 20.17V2h-2v18.17l-7.59-7.58L6 14l10 10l10-10z"></path></svg></div></button></a></div></div>
if __name__ == '__main__':

    parser = ArgumentParser()  
    parser.add_argument("--driven_audio", default='./examples/driven_audio/bus_chinese.wav', help="path to driven audio")
    parser.add_argument("--source_image", default='./examples/source_image/art_6.png', help="path to source image")
    parser.add_argument("--ref_eyeblink", default=None, help="path to reference video providing eye blinking")
    parser.add_argument("--ref_pose", default=None, help="path to reference video providing pose")
    parser.add_argument("--checkpoint_dir", default='./checkpoints', help="path to output")
    parser.add_argument("--result_dir", default='./results', help="path to output")
    parser.add_argument("--pose_style", type=int, default=1,  help="input pose style from [0, 46)")
    parser.add_argument("--batch_size", type=int, default=25,  help="the batch size of facerender")
    parser.add_argument("--size", type=int, default=256,  help="the image size of the facerender")
    parser.add_argument("--expression_scale", type=float, default=1.2,  help="the batch size of facerender")
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
    parser.add_argument("--facerender", default='pirender', choices=['pirender', 'facevid2vid']) 
    

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
    args.still = True
    '''server = GenVideoApi(args)
    server.app.run(host='0.0.0.0', port=9907)'''
    api = GenVideoApi(args)
    server = pywsgi.WSGIServer(('0.0.0.0', 9907), api.app)
    server.serve_forever()
