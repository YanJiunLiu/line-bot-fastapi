import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Header, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
# 這裡新增了 JoinEvent
from linebot.models import MessageEvent, TextMessage, TextSendMessage, JoinEvent

load_dotenv()

app = FastAPI()

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# 💡 模擬資料庫：紀錄群組狀態 (之後會換成 PostgreSQL)
# 狀態說明：pending (待設定), active (已啟用)
group_db = {}

@app.post("/callback")
async def callback(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "OK"

# --- 1. 處理加入群組事件 ---
@handler.add(JoinEvent)
def handle_join(event):
    group_id = event.source.group_id
    # 初始化群組狀態為待設定
    group_db[group_id] = {"status": "pending", "project_name": None}
    
    welcome_msg = "在使用查詢功能前，請先完成初始化。\n\n請輸入：\n『設定 [專案名稱]』"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=welcome_msg))

# --- 2. 處理訊息事件 (含鎖定邏輯) ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.source.type != 'group':
        return
        
    group_id = event.source.group_id
    user_text = event.message.text.strip()
    
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