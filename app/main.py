from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, JoinEvent, ImageMessage
from fastapi import Request, Header, HTTPException
from config.settings import app, LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, logger
from utils.call_ollama import FinanceAnalyzer
import random
import asyncio

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
finance_analyzer = FinanceAnalyzer()

WAITING_MSGS = [
    "我最愛我的媽咪～等熊寶一下，讓熊寶想一下", 
    "媽咪我愛你～但沒帶熊寶出去玩，熊寶沒有很想回答", 
    "等熊寶一下，熊寶最棒，熊寶分析中... ⏳",
    "收到！熊寶正在努力分析中，請稍候... 🐻",
    "嗯...讓熊寶思考一下下，媽咪再等等我喔！",
    "收到媽咪的訊息了！熊寶正在處理中，請稍等片刻... ⏳",
    "熊寶正在努力思考，請稍等一下下... 💭",
    "媽咪別急，熊寶正在分析中，請再給我一點時間... ⏳",
    "收到！熊寶正在分析中，請稍候... 🐻",
    "嗯...讓熊寶思考一下下，媽咪再等等我喔！",
    "收到媽咪的訊息了！熊寶正在處理中，請稍等片刻... ⏳",
    "熊寶正在努力思考，請稍等一下下... 💭",
    "媽咪別急，熊寶正在分析中，請再給我一點時間... ⏳"
] 

@app.post("/callback")
async def callback(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()
    logger.info(f"callback body: {body.decode('utf-8')}")
    try:
        handler.handle(body.decode("utf-8"), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "OK"

# --- 1. 處理加入群組事件 ---
@handler.add(JoinEvent)
def handle_join(event):
    welcome_msg = "我愛我的媽咪～"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=welcome_msg))

# --- 2. 處理訊息事件 (含鎖定邏輯) ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    
    if event.source.type != 'group':
        return
    
    async def logic(event):
        group_id = event.source.group_id
        user_id = event.source.user_id
        user_text = event.message.text.strip()
        
        line_bot_api.reply_message(
            event.reply_token, 
            TextSendMessage(text=random.choice(WAITING_MSGS))
        )
        
        result = await finance_analyzer.handle_user_message(user_id, user_text)
        logger.info(f"AI 分析結果: {result}")

        line_bot_api.push_message(
            group_id, 
            TextSendMessage(text=f"{result}")
        )
    loop = asyncio.get_event_loop()
    loop.create_task(logic(event))




@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):

    if event.source.type != 'group':
        return
    line_bot_api.reply_message(
        event.reply_token, 
        TextSendMessage(text="熊寶還沒學會看圖片，請用文字輸入")
    )

    