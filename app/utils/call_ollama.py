
from config import settings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser

import json
import uuid
from collections import defaultdict



class FinanceAnalyzer:
    def __init__(self):
        self.llm = ChatOpenAI(
            base_url=settings.OLLAMA_V1_URL,
            api_key="ollama",
            model=settings.OLLAMA_MODEL,
            temperature=0
        )
        settings.logger.info(f"Ollama 已連線: {settings.OLLAMA_V1_URL}")
        self.parser = JsonOutputParser()
        self.skills = self._load_file(settings.SKILL_FILE)
        self.redis_client = settings.redis_client

    def _load_file(self, filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            settings.logger.warning(f"找不到檔案: {filename}, 將不使用該檔案的內容")
            return ""

    async def preproccess(self, user_input: str, current_date: str):
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.skills),
            ("human", "{input}")
        ])

        chain = prompt | self.llm | self.parser
        
        try:
            result = await chain.ainvoke({
                "today": current_date,
                "input": user_input
            })
            settings.logger.info(f"模型解析結果: {result}")
            return result
        except Exception as e:
            settings.logger.error(f"模型解析失敗: {e}")
            return {"intent": "chat", "reply": "抱歉，我現在有點混亂，請再說一次。"}

    async def execute(self, user_input: str, history: list[str]=[]):
        formatted_history = []
        for msg in history:
            if msg.strip(): # 避免空白字串
                formatted_history.append(SystemMessage(content=f"歷史紀錄: {msg}"))
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一位處理資料的專家，請根據歷史紀錄和使用者的需求，修改歷史紀錄，並回覆使用者"),
            ("placeholder", "{history}"),
            ("human", "{input}")
        ])

        chain = prompt | self.llm | self.parser
        
        try:
            result = await chain.ainvoke({
                "today": CURRENT_DATE,
                "history": formatted_history,
                "input": user_input
            })
            settings.logger.info(f"模型解析結果: {result}")
            return result
        except Exception as e:
            settings.logger.error(f"模型解析失敗: {e}")
            return {"intent": "chat", "reply": "抱歉，我現在有點混亂，請再說一次。"}


    async def handle_user_message(self, user_id, user_text):
        # 1. 取得使用者當前狀態
        user_state_key = f"user:{user_id}:state"
        user_pending_key = f"user:{user_id}:pending"
        user_records_key = f"user:{user_id}:records"
        
        current_state = self.redis_client.get(user_state_key) or "idle"

        # 2. 讓 LLM 判斷意圖
        result = await self.chat(user_id, user_text)
        intent = result['intent']

        # --- 邏輯 A：處理「待確認」狀態 ---
        if current_state == "awaiting_confirm":
            if intent == "confirm" or user_text in ["對", "是", "好", "確認"]:
                # 從 Redis 提取暫存資料並正式寫入
                pending_data = self.redis_client.get(user_pending_key)
                self.redis_client.rpush(user_records_key, pending_data)
                
                # 清除狀態
                self.redis_client.set(user_state_key, "idle")
                self.redis_client.delete(user_pending_key)
                return "✅ 已成功入帳！"
            else:
                self.redis_client.set(user_state_key, "idle")
                self.redis_client.delete(user_pending_key)
                return "已取消操作。請問還有什麼我可以幫您的？"

        # --- 邏輯 B：處理「新增 (Create)」意圖 ---
        if intent == "create":
            save_data = json.dumps(result['data'], ensure_ascii=False)
            # 暫存到 Redis，不直接寫入帳本
            self.redis_client.set(user_pending_key, save_data)
            self.redis_client.set(user_state_key, "awaiting_confirm")
            msg = "好的，要幫您記錄以下資訊嗎？\n"
            for record in result['data']['records']:
                msg += (
                    "--------------------------------\n"
                    f"🔹 項目：{record.get('object')}\n"
                    f"🔹 金額：{record.get('money')}\n"
                    f"🔹 日期：{record.get('date')}\n"
                    f"🔹 購買人：{record.get('created_by')}\n"
                    "--------------------------------\n"
                )
            msg += "（請回覆：對/是）"
            return msg

        # --- 邏輯 C：處理「查詢 (Read)」意圖 ---
        elif intent == "read":
            history = self.redis_client.lrange(user_records_key, -5, -1) # 取最近 5 筆
            if not history: return "目前還沒有紀錄喔！"
            return "這是您最近的消費：\n" + "\n".join(history)

        # --- 邏輯 D：閒聊 ---
        else:
            return result['reply']
    
    
    async def chat(self, user_id, user_text, current_date):
        preproccess = await self.preproccess(user_text, current_date)
        settings.logger.info(f"preproccess {preproccess}")
        user_hash_key = f"user:{user_id}:records"
        if preproccess['intent'] == "create":
            msg = "好的，這是我幫您記錄的資訊：\n"
            mapping = {}
            for record in preproccess['data']['records']:
                if user_id == "Ue515c5951f6cf8372088cbc9c1bf57fb":
                    record['created_by'] = "爸比"
                else:
                    record['created_by'] = "媽咪"
                msg += (
                    "--------------------------------\n"
                    f"🔹 項目：{record.get('object')}\n"
                    f"🔹 金額：{record.get('money')}\n"
                    f"🔹 日期：{record.get('date')}\n"
                    f"🔹 購買人：{record.get('created_by')}\n"
                    "--------------------------------\n"
                )
                record_id = str(uuid.uuid4())[:8]
                record['id'] = record_id
                mapping[record_id] = json.dumps(record, ensure_ascii=False)
            if mapping:
                self.redis_client.hset(user_hash_key, mapping=mapping)
            return msg

        elif preproccess['intent'] == "delete":
            self.redis_client.hdel(user_hash_key, preproccess['delete_id'])
            return f"熊寶最棒，已刪除編號:{preproccess['delete_id']}"
            
        elif preproccess['intent'] == "update":
            raw_data = self.redis_client.hget(user_hash_key, preproccess['update_id'])
            if not raw_data:
                return "熊寶找不到該紀錄"
            record = json.loads(raw_data.encode('utf-8'))
            record.update(preproccess['update_data'])
            self.redis_client.hset(user_hash_key, preproccess['update_id'], json.dumps(record, ensure_ascii=False))
            return f"熊寶最棒，已更新編號:{preproccess}"
            
        elif preproccess['intent'] == "get":
            all_data = self.redis_client.hgetall(user_hash_key)
            records = [json.loads(v.encode('utf-8')) for v in all_data.values()]
            msg = "熊寶最棒，這是我幫您查詢的資訊：\n"
            for record in records:
                msg += (
                    "--------------------------------\n"
                    f"🔹 項目：{record.get('object')}\n"
                    f"🔹 金額：{record.get('money')}\n"
                    f"🔹 日期：{record.get('date')}\n"
                    f"🔹 購買人：{record.get('created_by')}\n"
                    f"🔹 分類：{record.get('category')}\n"
                    f"🔹 編號：{record.get('id')}\n"
                    "--------------------------------\n"
                )
            return msg
            
        elif preproccess['intent'] == "sum":
            all_records_raw = self.redis_client.hgetall(user_hash_key)
    
            if not all_records_raw:
                return "🐻 找不到任何紀錄呢！"

            total_sum = 0
            match_count = 0
            start_date = preproccess['sum'].get('start_date', '1999-01-01')
            end_date = preproccess['sum'].get('end_date', '2099-12-31')
            details = []

            for record_json in all_records_raw.values():
                record = json.loads(record_json.encode('utf-8'))
                r_date = record.get('date', '') # 格式：2026-03-10
                
                if start_date <= r_date <= end_date:
                    amount = record.get('money', 0) or 0
                    total_sum += amount
                    match_count += 1
                    details.append(f"· {r_date} {record.get('object')} ${amount}")

            if match_count == 0:
                return f"📍 在 {start_date} 到 {end_date} 之間沒有消費紀錄喔！"

            msg = f"🗓️ 【區間統計報告】\n"
            msg += f"期間：{start_date} ➡️ {end_date}\n"
            msg += "--------------------------------\n"
            
            # 只列出前 10 筆明細，避免訊息過長
            msg += "\n".join(details[:10])
            if len(details) > 10:
                msg += f"\n...等共 {len(details)} 筆紀錄"
                
            msg += "\n--------------------------------\n"
            msg += f"💰 區間總計：${total_sum:,.0f}"
            
            return msg
            
        else:
            return preproccess['reply']
            

