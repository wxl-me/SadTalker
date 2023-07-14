import os, sys
import gradio as gr
from src.gradio_demo import SadTalker  
import push_inference

try:
    import webui  # in webui
    in_webui = True
except:
    in_webui = False


def toggle_audio_file(choice):
    if choice == False:
        return gr.update(visible=True), gr.update(visible=False)
    else:
        return gr.update(visible=False), gr.update(visible=True)
    
def ref_video_fn(path_of_ref_video):
    if path_of_ref_video is not None:
        return gr.update(value=True)
    else:
        return gr.update(value=False)

def sadtalker_demo(checkpoint_path='checkpoints', config_path='src/config', warpfn=None):

    sad_talker = SadTalker(checkpoint_path, config_path, lazy_load=True)

    with gr.Blocks(analytics_enabled=False) as sadtalker_interface:

        if not in_webui:
            gr.Markdown("<div align='center'> <h2> 音频&图片生成视频Demo &nbsp;&nbsp; <a href='https://www.aimall-tech.com/'>--BY Aimall</a> </h2> ")
        
        with gr.Row().style(equal_height=False):
            with gr.Column(variant='panel'):
                with gr.Tabs(elem_id="sadtalker_source_image"):
                    with gr.TabItem('源图像'):
                        with gr.Row():
                            source_image = gr.Image(label="上传源图像", source="upload", type="filepath", elem_id="img2img_image").style(height=256)
                            gen_video = gr.Video(label="已生成视频", format="mp4").style(width=256)

                gr.Markdown("可供选择的生成方式:  1. 仅音频 2. 音频+参考视频 3. IDLE模式 4.仅参考视频")
                with gr.Tabs(elem_id="sadtalker_driven_audio"):
                    with gr.TabItem('音频选择'):
                        with gr.Row():
                            driven_audio = gr.Audio(label="输入音频", source="upload", type="filepath").style(height=200)
                            driven_audio_no = gr.Audio(label="使用IDLE模式，无需添加音频", source="upload", type="filepath", visible=False)
                            with gr.Column():
                                use_idle_mode = gr.Checkbox(label="开启IDLE模式")
                                length_of_audio = gr.Number(value=5, label="需要生成的视频长度(s)")
                                use_idle_mode.change(toggle_audio_file, inputs=use_idle_mode, outputs=[driven_audio, driven_audio_no]) # todo
                    with gr.TabItem('语音转文字'):
                        #if sys.platform != 'win32' and not in_webui:
                        #with gr.Accordion('使用文本转语音', open=False):
                        from src.utils.text2speech import TTSTalker_API
                        tts_talker = TTSTalker_API()
                        with gr.Column(variant='panel'):
                            talker = gr.Radio(['女声小元', '欧美女声'], value='女生小元',type="index", label='参考视频',info="如何参考视频？")
                            input_text = gr.Textbox(label="输入文本以转语音", lines=5, placeholder="请输入文本，可选择的音色有：1、女声小元 2、欧美女声")
                            tts = gr.Button('生成音频',elem_id="sadtalker_audio_generate", variant='primary')
                            tts.click(fn=tts_talker.test, inputs=[input_text,talker], outputs=[driven_audio])
                    with gr.TabItem('参考选择'):
                        with gr.Row():
                            ref_video = gr.Video(label="参考视频", source="upload", type="filepath", elem_id="vidref").style(width=512,height=200)
                            with gr.Column():
                                use_ref_video = gr.Checkbox(label="参考视频生成")
                                ref_info = gr.Radio(['pose', 'blink','pose+blink', 'all'], value='pose', label='如何参考视频')
                            ref_video.change(ref_video_fn, inputs=ref_video, outputs=[use_ref_video]) # todo
                    with gr.TabItem('持续生成'):
                        generate_continous = gr.Button('持续生成', elem_id="sadtalker_generate_continuous", variant='primary')

            with gr.Column(variant='panel'): 
                with gr.Tabs(elem_id="sadtalker_checkbox"):
                    with gr.TabItem('设置'):
                        with gr.Column(variant='panel'):
                            # width = gr.Slider(minimum=64, elem_id="img2img_width", maximum=2048, step=8, label="Manually Crop Width", value=512) # img2img_width
                            # height = gr.Slider(minimum=64, elem_id="img2img_height", maximum=2048, step=8, label="Manually Crop Height", value=512) # img2img_width
                            with gr.Row():
                                pose_style = gr.Slider(minimum=0, maximum=45, step=1, label="姿势选择", value=0) #
                                exp_weight = gr.Slider(minimum=0, maximum=3, step=0.1, label="表情系数", value=1) # 
                                blink_every = gr.Checkbox(label="use eye blink", value=True)
                            preprocess_type = gr.Radio(['crop', 'resize','full', 'extcrop', 'extfull'], value='crop', label='源图像预处理')                      
                            with gr.Row():     
                                size_of_image = gr.Radio([256, 512], value=256, label='脸部分辨率') #
                                facerender = gr.Radio(['facevid2vid','pirender'], value='facevid2vid', label='质量模式/速度模式')
                                with gr.Column():
                                    batch_size = gr.Slider(label="生成速度(Batch Size)", step=1, maximum=30, value=2)
                                    enhancer = gr.Checkbox(label="是否使用脸部增强")
                                    is_still_mode = gr.Checkbox(label="静止模式(仅在`full`)")   
                                
                            submit = gr.Button('生成', elem_id="sadtalker_generate", variant='primary')
        
        submit.click(
                fn=warpfn(sad_talker.test) if warpfn else sad_talker.test,
                inputs=[source_image,
                        driven_audio,
                        preprocess_type,
                        is_still_mode,
                        enhancer,
                        batch_size,                            
                        size_of_image,
                        pose_style,
                        facerender,
                        exp_weight,
                        use_ref_video,
                        ref_video,
                        ref_info,
                        use_idle_mode,
                        length_of_audio,
                        blink_every
                        ], 
                outputs=[gen_video]
                )
        generate_continous.click(fn=push_inference.launch,
                inputs=[
                        source_image,
                        driven_audio,
                        preprocess_type,
                        is_still_mode,
                        enhancer,
                        batch_size,                            
                        size_of_image,
                        pose_style,
                        facerender,
                        exp_weight,
                        use_ref_video,
                        ref_video,
                        ref_info,
                        use_idle_mode,
                        length_of_audio,
                        blink_every
                        ],)
    return sadtalker_interface
 

if __name__ == "__main__":

    demo = sadtalker_demo()
    demo.queue()
    demo.launch()


