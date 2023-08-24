## **使用方式**

### main_API_inference.py 数字人生成程序
运行：python3 main_API_inference.py
参数：（仅介绍重点参数，没介绍的按默认即可）

1. --driven_audio 驱动音频（无需选择，因为使用的是TTS合成的语音）
  
2. --source_image 选择一张人脸图像，以生成对应的视频
  
3. --ref_eyeblink 参考视频中的眨眼生成视频 （一般不选）
  
4. --ref_pose 参考视频中的动作姿势生成（一般不选）
  
5. --pose_style 头像动作风格，可以调整，但是效果是随机的，范围在[0,46)
  
6. --expression_scale 表情幅度，越大表情越夸张
  
7. --input_yaw / --input_pitch / --input_roll 动作翻转，一般不选
  
8. --enhancer 是否选择超分，选择后很慢，无法实时生成
  
9. --still 静止模式，仅嘴巴和眼睛会动，头像不会动
  
10. --facerender 合成算法，pirender比较快但是质量差，facevid2vid质量高速度慢，默认选pirender

### laucher.py       gradio启动入口
运行：python3 laucher.py
line197     from app_sadtalker_wxl import sadtalker_demo 
            可以改成    from app_sadtalker import sadtalker_demo  即可使用原版demo

### app_sadtalker_wxl.py    数字人客户端程序
运行：python3 app_sadtalker_wxl.py
提供3个问题供选择： 1、你好  2、你会干什么  3、介绍一下深圳
输入格式：问题序号(1-3) 音色(0-842) 音调(-12~12)
    例如： 1 0 0
    注意：音色0表示小元TTS，音色1表示英文TTS，其余音色通过卢家乐提供。音调变换选择也是由卢家乐提供，无法工作时请咨询他

## **方案介绍**

注意：下面的表述中，**视频帧代表图像，视频代表图像+音频**

### **方案1：每秒生成视频并推流至服务器，需要拉流播放**

**子方案1：**推流使用ffmpeg将一秒的视频直接推流，需要使用os.system（‘ffmpeg ***’），此时推流的内容是mp4视频文件
**子方案2：**将视频帧和音频帧分别推流到两个网址，然后使用ffmpeg命令将视频和音频进行合流到一个新的网址(通过管道持续推流，而不需要每次进行os.system调用推流命令)，此时推流的是视频帧和音频数据
缺点：

1. 需要搭建推流服务器，延迟略高
  
2. 需要控制推流的时间，拉流播放器操作麻烦且容易失败
  
3. 只能在手机APP（IP摄像头）上播放，电脑VLC播放器播放失败
  
4. 卡顿感，视频秒与秒之间有跳跃的感觉，不连贯
  

操作方法：

1. 搭建nginx推流服务器，参考https://blog.csdn.net/weixin_53936496/article/details/124061778
  
2. 运行主程序 python3 API_inference.py
  
3. 手机可以用IP摄像头 APP播放，电脑端使用VLC播放器播放
  

  

### **方案2：每秒生成视频，发送到客户端，客户端播放每秒的视频**

缺点：

1. 没有找到很好的方法将每秒的视频连续播放
  
2. 使用ffmpeg 或 mplayer 持续播放视频遇到困难，难以解决
  
3. 曾尝试将视频和音频发送到ffmpeg播放管道中，但是有些复杂，遂放弃
  

  

### **方案3：（当前方案）**

**服务端：按每句话生成视频，将视频帧和音频使用Flask的流式（SSE）发送到客户端**
**客户端：通过opencv和playsound播放视频和音频（多线程实现）**
缺点：

1. 视频帧和音频帧分开播放，代码编写复杂
  
2. 时间长的话音视频不同步（思路：对每一组音视频，添加flag使其同时播放，当前仅用视频帧队列持续播放，没有与音频的时间联动）
  
3. 程序实现略微复杂，多线程容易出现bug
  

注意：opencv不能在子线程中播放，因此与语音唤醒程序连接时，需要用子进程调用