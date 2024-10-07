# 阿里云百炼
import json

from openai import OpenAI, api_key
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(verbose=True)


def get_response(context:str):
    client = OpenAI(
        api_key=os.getenv("ALIYUN_API_KEY"),  # 如果您没有配置环境变量，请在此处用您的API Key进行替换

        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 填写DashScope SDK的base_url
    )

    completion = client.chat.completions.create(
        model="qwen-plus",
        messages=[{'role': 'system', 'content': '你是一个幽默风趣的聊天机器人，请使用中文回答问题。'},
                  {'role': 'user', 'content': context}]
    )
    data = json.loads(completion.model_dump_json())
    return data.get("choices")[0].get("message").get("content")

