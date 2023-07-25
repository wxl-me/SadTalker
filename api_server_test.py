from flask import Flask,Response,make_response,send_from_directory,jsonify
import time,json,random,base64
from gevent import pywsgi
app = Flask("__main__")
@app.route("/test",methods=["GET","POST"])
def call_test():
    def eventStream():
        for i in range(10):
            # 1 SSE 返回格式是json字符串，要使用yield返回，字符串后面一定要跟随 \n\n
            print(i,' : ')
            with open('return_video.mp4', 'rb') as f:
                yield 'data:'+json.dumps({'time': i, 'value': str(base64.b64encode(f.read()))})+'\n\n'
            #yield 'data:'+json.dumps({'time': i, 'value': 'aaaaaaaaaaaaaaaa'})+'\n\n'
            #time.sleep(1)
    return Response(eventStream(), mimetype="text/event-stream")

server = pywsgi.WSGIServer(('0.0.0.0', 9907), app)
server.serve_forever()