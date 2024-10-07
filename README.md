# FeishuAiBot 飞书AI机器人

## Node.js 版本

https://github.com/essesoul/FeishuAiBot/tree/main/js 

修改自 https://github.com/bestony/ChatGPT-Feishu

----

## Python 版本（更新中）

https://github.com/essesoul/FeishuAiBot

### 使用方法

#### 创建一个飞书开放平台应用，并获取到 APPID 和 Secret

访问 [开发者后台](https://open.feishu.cn/app?lang=zh-CN)，创建一个名为 **ChatGPT** 的应用，并上传应用头像。创建完成后，访问【凭证与基础信息】页面，复制 APPID 和 Secret 备用。

![image-20230210012031179](assets\202302100120339.png)

#### 开启机器人能力

打开应用的机器人应用功能

![image-20230210012110735](assets\202302100121008.png)

#### 修改配置文件

复制 `.env_example` 文件内容到新文件 `.env` 中

示例：

```
#  飞书 APPID
FS_APPID=""
# 飞书密钥
FS_SECRET=""
# 飞书机器人名称
FS_BOTNAME=""

# 腾讯混元
HUNYUAN_API_KEY=""

# 阿里云通义
ALIYUN_API_KEY=""
```

运行 `pip install -r requirements.txt` 安装依赖包

