# 飞书机器人
import threading

from flask import Flask, request, jsonify
import os
import json
import requests
from dotenv import load_dotenv
from lark_oapi.api.im.v1 import ReplyMessageRequest, ReplyMessageRequestBody, ReplyMessageResponse

load_dotenv(verbose=True)
app = Flask(__name__)

# 配置
FEISHU_APP_ID = os.getenv('FS_APPID')
FEISHU_APP_SECRET = os.getenv('FS_SECRET')
FEISHU_BOTNAME = os.getenv('FS_BOTNAME')
OPENAI_KEY = os.getenv('HUNYUAN_API_KEY')
OPENAI_MODEL = os.getenv('MODEL', 'hunyuan-pro')
OPENAI_MAX_TOKEN = int(os.getenv('MAX_TOKEN', 1024))

# https://github.com/larksuite/oapi-sdk-python
import lark_oapi as lark



# 日志辅助函数
def logger(param):
    print(f"[CF] {param}")


# 回复消息
def reply(message_id, content):
    client = lark.Client.builder() \
        .app_id(FEISHU_APP_ID) \
        .app_secret(FEISHU_APP_SECRET) \
        .build()
    reply_request = ReplyMessageRequest.builder() \
        .message_id(message_id) \
        .request_body(ReplyMessageRequestBody.builder()
                      .content(json.dumps({"text": content}))
                      .msg_type("text")
                      .reply_in_thread(False)
                      # .uuid("")
                      .build()) \
        .build()
    response: ReplyMessageResponse = client.im.v1.message.reply(reply_request)
    if not response.success():
        lark.logger.error(
            f"client.im.v1.message.reply failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
        return
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    return


# 构造用户会话
def build_conversation(question):
    prompt = [{"role": "user", "content": question}]
    return prompt


# 获取回复
def get_openai_reply(prompt):
    url = "https://api.hunyuan.cloud.tencent.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": OPENAI_MODEL,
        "messages": prompt
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 429:
        return '问题太多了，我有点眩晕，请稍后再试'
    return response.json()['choices'][0]['message']['content'].replace("\n\n", "")


# 处理回复
def handle_reply(user_input, message_id):
    question = user_input['text'].replace("@_user_1", "")
    logger(f"question: {question}")
    prompt = build_conversation(question)
    openai_response = get_openai_reply(prompt)
    reply(message_id, openai_response)
    return {"code": 0}


def webhook_task(req_json):
    params = req_json
    if params.get('encrypt'):
        logger("user enable encrypt key")
    if params.get('type') == 'url_verification':
        logger("deal url_verification")
    if params['header']['event_type'] == 'im.message.receive_v1':
        message_id = params['event']['message']['message_id']
        if params['event']['message']['chat_type'] == 'p2p':
            if params['event']['message']['message_type'] != 'text':
                reply(message_id, "暂不支持其他类型的提问")
                logger("skip and reply not support")
            user_input = json.loads(params['event']['message']['content'])
            handle_reply(user_input, message_id)
        if params['event']['message']['chat_type'] == 'group':
            if not params['event']['message'].get('mentions') or len(params['event']['message']['mentions']) == 0:
                logger("not process message without mention")
            if params['event']['message']['mentions'][0]['name'] != FEISHU_BOTNAME:
                logger("bot name not equal first mention name ")
            user_input = json.loads(params['event']['message']['content'])
            handle_reply(user_input, message_id)


@app.route('/webhook', methods=['POST'])
def webhook():
    threading.Thread(target=webhook_task, args=(request.json,)).start()
    return jsonify({"code": 200}), 200


if __name__ == '__main__':
    app.run(port=15080, debug=False)
