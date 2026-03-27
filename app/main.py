from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
# 這裡新增了 JoinEvent
from linebot.models import MessageEvent, TextMessage, TextSendMessage, JoinEvent, ImageMessage
from fastapi import Request, Header, HTTPException
from config.settings import app, LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, logger

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

group_db = {}

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
    logger.info(f"event: {event}")
    group_id = event.source.group_id
    user_text = event.message.text.strip()
    logger.info(f"user_text: {user_text}")

    current_config = group_db.get(group_id, {"status": "pending"})
    
    if current_config["status"] == "pending":
        if user_text.startswith("設定"):
            project_name = user_text[2:].strip()
            if not project_name:
                reply = "請輸入有效的專案名稱。\n範例：設定 秘密專案"
            else:
                group_db[group_id] = {"status": "active", "project_name": project_name}
                reply = f"設定成功！\n專案：{project_name}\n現在您可以開始使用「查詢」功能了。"
        else:
            reply = "請先完成設定才能開始使用。\n請輸入：設定 [專案名稱]"
    
    else:
        if user_text.startswith("查詢"):
            keyword = user_text[2:].strip()
            project = current_config["project_name"]
            reply = f"🔍 正在專案【{project}】中搜尋：{keyword}"
        else:
            return 

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))



@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    if event.source.type != 'group':
        return
    # 1. 取得訊息 ID
    message_id = event.message.id
    logger.info(f"收到圖片訊息，ID: {message_id}")

    # 2. 向 LINE 請求圖片內容
    message_content = line_bot_api.get_message_content(message_id)
    
    # 3. 將內容讀取為二進位格式 (bytes)
    image_bytes = b""
    for chunk in message_content.iter_content():
        image_bytes += chunk
    
    # 現在 image_bytes 就是圖片的原始資料了！
    logger.info(f"成功取得圖片，大小: {len(image_bytes)} bytes")

    # 回覆使用者
    line_bot_api.reply_message(
        event.reply_token, 
        TextSendMessage(text=f"收到圖片，正在分析中...")
    )