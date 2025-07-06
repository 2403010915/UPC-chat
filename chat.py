from flask import Flask, request, Response, stream_with_context
import time
import json

app = Flask(__name__)

@app.route('/stream_openai_generate', methods=['POST'])
def stream_openai_generate():
    data = request.get_json()
    user_messages = data.get('messages', [])
    new_message = data.get('newMessage', '')

    # 伪造推理内容和AI回复
    reason = f"推理内容：分析用户输入“{new_message}”的情感和意图。"
    ai_response = f"您好，您刚才说的是：“{new_message}”。我已经收到并理解您的问题。"

    def generate():
        # 推理内容流式返回
        for c in reason:
            yield f'data: {json.dumps({"reason": True, "text": c})}\n'
            time.sleep(0.03)
        yield '\n'
        # AI回复流式返回
        for c in ai_response:
            yield f'data: {json.dumps({"reason": False, "text": c})}\n'
            time.sleep(0.03)
        yield '\n'

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(port=8000, debug=True)