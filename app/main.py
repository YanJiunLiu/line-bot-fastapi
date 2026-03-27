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
def _get_waiting_msg(user_id):
    if user_id == "Ue515c5951f6cf8372088cbc9c1bf57fb":
        human = "爸比"
    else:
        human = "媽咪"
    WAITING_MSGS = [
        f"我最愛我的{human}～等熊寶一下，讓熊寶想一下", 
        f"{human}我愛你～但沒帶熊寶出去玩，熊寶沒有很想回答", 
        f"等熊寶一下，熊寶最棒，熊寶處理中... ⏳",
        f"收到！熊寶正在努力處理中，請稍候... 🐻",
        f"嗯...讓熊寶思考一下下，{human}再等等我喔！",
        f"收到{human}的訊息了！熊寶正在處理中，請稍等片刻... ⏳",
        f"熊寶正在努力思考，請稍等一下下... 💭",
        f"{human}別急，熊寶正在處理中，請再給我一點時間... ⏳",
        f"收到！熊寶正在處理中，請稍候... 🐻",
        f"嗯...讓熊寶思考一下下，{human}再等等我喔！",
        f"收到{human}的訊息了！熊寶正在處理中，請稍等片刻... ⏳",
        f"熊寶正在努力思考，請稍等一下下... 💭",
        f"{human}別急，熊寶正在處理中，請再給我一點時間... ⏳",
        f"收到！熊寶正在處理中，請稍候... 🐻",
        f"嗯...讓熊寶思考一下下，{human}再等等我喔！",
        f"收到{human}的訊息了！熊寶正在處理中，請稍等片刻... ⏳",
        f"熊寶正在努力思考，請稍等一下下... 💭",
        f"{human}別急，熊寶正在處理中，請再給我一點時間... ⏳"
    ] 
    return random.choice(WAITING_MSGS)
  


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
        logger.info(f"user_id: {user_id}")
        user_text = event.message.text.strip()
        
        line_bot_api.reply_message(
            event.reply_token, 
            TextSendMessage(text=_get_waiting_msg(user_id))
        )
        
        result = await finance_analyzer.chat(user_id, user_text)

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
        TextSendMessage(text="熊寶還沒學會看圖片，我最愛我的媽咪～")
    )

    