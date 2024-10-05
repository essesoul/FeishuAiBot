import json
import os
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv

load_dotenv(verbose=True)


def get_response(context: str):
    client = OpenAI(
        api_key=os.environ.get("HUNYUAN_API_KEY"),  # 混元 APIKey
        base_url="https://api.hunyuan.cloud.tencent.com/v1",  # 混元 endpoint
    )

    completion = client.chat.completions.create(
        model="hunyuan-pro",
        messages=[{'role': 'system', 'content': '你是一个幽默风趣的聊天机器人，请使用中文回答问题。'},
                  {
                      "role": "user",
                      "content": context,
                  },
                  ],
    )
    data = json.loads(completion.model_dump_json())
    return data.get("choices")[0].get("message").get("content")
