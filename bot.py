# 飞书机器人
from flask import Flask, request, jsonify
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv(verbose=True)
app = Flask(__name__)

# 配置
FEISHU_APP_ID = os.getenv('FS_APPID')
FEISHU_APP_SECRET = os.getenv('FS_SECRET')
FEISHU_BOTNAME = os.getenv('FS_BOTNAME')
OPENAI_KEY = os.getenv('HUNYUAN_API_KEY')
OPENAI_MODEL = os.getenv('MODEL', 'hunyuan-pro')
OPENAI_MAX_TOKEN = int(os.getenv('MAX_TOKEN', 1024))


# 日志辅助函数
def logger(param):
    print(f"[CF] {param}")


# 回复消息
def reply(message_id, content):
    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"
    headers = {
        "Authorization": f"Bearer {FEISHU_APP_SECRET}",
        "Content-Type": "application/json"
    }
    data = {
        "content": json.dumps({"text": content}),
        "msg_type": "text"
    }
    response = requests.post(url, headers=headers, json=data)
    print(response.json())
    return response.json()


# 构造用户会话
def build_conversation(question):
    prompt = [{"role": "user", "content": question}]
    return prompt



# 指令处理
def cmd_process(cmd_params):
    if cmd_params['action'].startswith("/image"):
        prompt = cmd_params['action'][7:]
        url = get_openai_image_url(prompt)
        reply(cmd_params['messageId'], url)
        return
    if cmd_params['action'] == "/help":
        cmd_help(cmd_params['messageId'])
    else:
        cmd_help(cmd_params['messageId'])
    return {"code": 0}


# 帮助指令
def cmd_help(message_id):
    help_text = """ChatGPT 指令使用指南

Usage:
    /image ${提示词} 根据提示词生成图片
  """
    reply(message_id, help_text)


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
def handle_reply(user_input, session_id, message_id):
    question = user_input['text'].replace("@_user_1", "")
    logger(f"question: {question}")
    action = question.strip()
    if action.startswith("/"):
        return cmd_process({"action": action, "sessionId": session_id, "messageId": message_id})
    prompt = build_conversation(question)
    openai_response = get_openai_reply(prompt)
    reply(message_id, openai_response)
    return {"code": 0}


@app.route('/webhook', methods=['POST'])
def webhook():
    params = request.json
    # print(params)
    if params.get('encrypt'):
        logger("user enable encrypt key")
        return jsonify({"code": 1, "message": {"zh_CN": "你配置了 Encrypt Key，请关闭该功能。",
                                               "en_US": "You have open Encrypt Key Feature, please close it."}})
    if params.get('type') == 'url_verification':
        logger("deal url_verification")
        return jsonify({"challenge": params['challenge']})
    if not params.get('header') or request.headers.get('X-OpenAI-Debug'):
        logger("enter doctor")
        return jsonify(doctor())
    if params['header']['event_type'] == 'im.message.receive_v1':
        message_id = params['event']['message']['message_id']
        chat_id = params['event']['message']['chat_id']
        sender_id = params['event']['sender']['sender_id']['user_id']
        session_id = f"{chat_id}{sender_id}"
        if params['event']['message']['chat_type'] == 'p2p':
            if params['event']['message']['message_type'] != 'text':
                reply(message_id, "暂不支持其他类型的提问")
                logger("skip and reply not support")
                return jsonify({"code": 0})
            user_input = json.loads(params['event']['message']['content'])
            return jsonify(handle_reply(user_input, session_id, message_id))
        if params['event']['message']['chat_type'] == 'group':
            if not params['event']['message'].get('mentions') or len(params['event']['message']['mentions']) == 0:
                logger("not process message without mention")
                return jsonify({"code": 0})
            if params['event']['message']['mentions'][0]['name'] != FEISHU_BOTNAME:
                logger("bot name not equal first mention name ")
                return jsonify({"code": 0})
            user_input = json.loads(params['event']['message']['content'])
            return jsonify(handle_reply(user_input, session_id, message_id))
    logger("return without other log")
    return jsonify({"code": 2})


@app.route('/doctor', methods=['GET'])
def doctor():
    if FEISHU_APP_ID == "":
        return jsonify({"code": 1, "message": {"zh_CN": "你没有配置飞书应用的 AppID，请检查 & 部署后重试",
                                               "en_US": "Here is no FeiSHu APP id, please check & re-Deploy & call again"}})
    if not FEISHU_APP_ID.startswith("cli_"):
        return jsonify({"code": 1, "message": {
            "zh_CN": "你配置的飞书应用的 AppID 是错误的，请检查后重试。飞书应用的 APPID 以 cli_ 开头。",
            "en_US": "Your FeiShu App ID is Wrong, Please Check and call again. FeiShu APPID must Start with cli"}})
    if FEISHU_APP_SECRET == "":
        return jsonify({"code": 1, "message": {"zh_CN": "你没有配置飞书应用的 Secret，请检查 & 部署后重试",
                                               "en_US": "Here is no FeiShu APP Secret, please check & re-Deploy & call again"}})
    if FEISHU_BOTNAME == "":
        return jsonify({"code": 1, "message": {"zh_CN": "你没有配置飞书应用的名称，请检查 & 部署后重试",
                                               "en_US": "Here is no FeiShu APP Name, please check & re-Deploy & call again"}})
    if OPENAI_KEY == "":
        return jsonify({"code": 1, "message": {"zh_CN": "你没有配置 OpenAI 的 Key，请检查 & 部署后重试",
                                               "en_US": "Here is no OpenAI Key, please check & re-Deploy & call again"}})
    if not OPENAI_KEY.startswith("sk-"):
        return jsonify({"code": 1,
                        "message": {"zh_CN": "你配置的 OpenAI Key 是错误的，请检查后重试。OpenAI 的 KEY 以 sk- 开头。",
                                    "en_US": "Your OpenAI Key is Wrong, Please Check and call again. FeiShu APPID must Start with cli"}})
    return jsonify({"code": 0, "message": {"zh_CN": "✅ 配置成功，接下来你可以在飞书应用当中使用机器人来完成你的工作。",
                                           "en_US": "✅ Configuration is correct, you can use this bot in your FeiShu App"},
                    "meta": {"FEISHU_APP_ID", "OPENAI_MODEL", "OPENAI_MAX_TOKEN", "FEISHU_BOTNAME"}})


if __name__ == '__main__':
    app.run(port=15080, debug=True)
