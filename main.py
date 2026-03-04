import os 
from dotenv import load_dotenv 
from fastapi import FastAPI, Request, Header, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

load_dotenv()

app = FastAPI()

# 請替換成你在 LINE Developer 取得的資訊
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# 填入你的 Token 與 Secret
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.post("/callback")
async def callback(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 取得 groupId 的語法
    group_id = event.source.group_id if event.source.type == 'group' else '非群組訊息'
    print(f"當前群組 ID: {group_id}")
    # 這邊之後會加入資料庫查詢邏輯
    user_text = event.message.text
    print(user_text)
    # 這裡可以加入判斷：如果是查詢指令，就去翻資料庫
    if user_text.startswith("查詢"):
        reply = f"收到！你要查詢的是：{user_text[2:].strip()}"
    else:
        reply = "請輸入「查詢 + 關鍵字」來搜尋資料庫喔！"
        
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )