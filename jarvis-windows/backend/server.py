# import asyncio, json, httpx, edge_tts, base64, tempfile
# from fastapi import FastAPI, WebSocket
# from fastapi.staticfiles import StaticFiles
# from modules.memory import init_db, save, search, recent
# from modules.calendar_win import get_events
# from modules.email_win import get_emails
# from modules.browser import search_web, browse
# from modules.notes import create_note, list_notes, read_note
# from modules.system_actions import run_powershell, open_app

# app = FastAPI()
# init_db()

# OLLAMA_URL  = "http://localhost:11434/api/chat"
# FAST_MODEL  = "llama3"
# DEEP_MODEL  = "llama3"
# TTS_VOICE   = "en-GB-RyanNeural"   # change to your preferred voice

# SYSTEM_PROMPT = """You are JARVIS, a voice AI assistant running locally on Windows.
# You are concise — voice responses should be 1-3 sentences unless asked for more.
# You can use these actions by responding with JSON action blocks like:
# {"action": "calendar"} — get calendar events
# {"action": "email"} — read emails
# {"action": "search", "query": "..."} — search the web
# {"action": "browse", "url": "..."} — open a URL
# {"action": "note_create", "title": "...", "content": "..."} — save a note
# {"action": "note_list"} — list notes
# {"action": "powershell", "cmd": "..."} — run a Windows command
# {"action": "open_app", "name": "..."} — open an application
# If no action needed, respond normally."""

# async def ollama_chat(messages: list, model: str = FAST_MODEL) -> str:
#     async with httpx.AsyncClient(timeout=60) as client:
#         resp = await client.post(OLLAMA_URL, json={
#             "model": model,
#             "messages": messages,
#             "stream": False
#         })
#         return resp.json()["message"]["content"]

# async def tts_to_base64(text: str) -> str:
#     communicate = edge_tts.Communicate(text, TTS_VOICE)
#     with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
#         tmp = f.name
#     await communicate.save(tmp)
#     with open(tmp, "rb") as f:
#         return base64.b64encode(f.read()).decode()

# def handle_action(action_json: dict) -> str:
#     act = action_json.get("action", "")
#     if act == "calendar":
#         return json.dumps(get_events())
#     elif act == "email":
#         return json.dumps(get_emails())
#     elif act == "search":
#         return search_web(action_json.get("query", ""))
#     elif act == "browse":
#         return browse(action_json.get("url", ""))
#     elif act == "note_create":
#         path = create_note(action_json.get("title","note"), action_json.get("content",""))
#         return f"Note saved to {path}"
#     elif act == "note_list":
#         return json.dumps(list_notes())
#     elif act == "powershell":
#         return run_powershell(action_json.get("cmd",""))
#     elif act == "open_app":
#         return open_app(action_json.get("name",""))
#     return "Unknown action."

# @app.websocket("/ws")
# async def websocket_endpoint(ws: WebSocket):
#     await ws.accept()
#     history = []

#     while True:
#         data = await ws.receive_json()
#         user_msg = data.get("text", "")
#         deep     = data.get("deep", False)

#         save("user", user_msg)
#         context = recent(10)
#         history = [{"role": m["role"], "content": m["content"]} for m in context]
#         history.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

#         model = DEEP_MODEL if deep else FAST_MODEL
#         await ws.send_json({"type": "thinking"})

#         reply = await ollama_chat(history, model)

#         # check if reply contains an action
#         try:
#             start = reply.find("{")
#             end   = reply.rfind("}") + 1
#             if start != -1:
#                 action_data = json.loads(reply[start:end])
#                 if "action" in action_data:
#                     action_result = handle_action(action_data)
#                     history.append({"role": "assistant", "content": reply})
#                     history.append({"role": "user",      "content": f"Action result: {action_result}"})
#                     reply = await ollama_chat(history, model)
#         except (json.JSONDecodeError, ValueError):
#             pass

#         save("assistant", reply)
#         audio_b64 = await tts_to_base64(reply)
#         await ws.send_json({"type": "response", "text": reply, "audio": audio_b64})

# app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")




import asyncio, json, httpx, edge_tts, base64, tempfile, os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from modules.memory import init_db, save, recent
from modules.calendar_win import get_events
from modules.email_win import get_emails
from modules.browser import search_web, browse
from modules.notes import create_note, list_notes, read_note
from modules.system_actions import run_powershell, open_app

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

OLLAMA_URL = "http://localhost:11434/api/chat"
FAST_MODEL = "gemma:latest"
DEEP_MODEL = "llama3"
TTS_VOICE = "en-GB-RyanNeural"

# ------------------ SYSTEM PROMPT ------------------

SYSTEM_PROMPT = """You are JARVIS, a voice AI assistant running on Windows.

If an action is needed, respond with ONLY pure JSON, no other text.

Available actions:
- {"action": "powershell", "cmd": "command"}
- {"action": "open_app", "name": "app_name"}
- {"action": "browse", "url": "https://..."}
- {"action": "note_create", "title": "title", "content": "content"}
- {"action": "note_list"}
- {"action": "note_read", "title": "title"}
- {"action": "search", "query": "query"}
- {"action": "calendar"}
- {"action": "email"}

Rules:
1. If responding with JSON action, send ONLY the JSON object, nothing else
2. If no action needed, respond naturally in 1-3 sentences
3. Do NOT use ** or markdown formatting
4. Keep voice responses brief and clear
"""

# ------------------ OLLAMA CHAT ------------------

async def ollama_chat(messages: list, model: str = FAST_MODEL) -> str:
    """Chat with Ollama - handles both streaming and non-streaming"""
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                OLLAMA_URL,
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False
                },
                timeout=120
            )
            
            if resp.status_code != 200:
                print(f"Ollama error: {resp.status_code}")
                return "Sorry, I'm having trouble thinking right now."
            
            data = resp.json()
            full_reply = data.get("message", {}).get("content", "").strip()
            
            if not full_reply:
                return "I didn't understand that."
            
            print(f"[OLLAMA] {model}: {full_reply[:100]}")
            return full_reply
            
    except Exception as e:
        print(f"Ollama chat error: {str(e)}")
        return "Sorry, something went wrong."

# ------------------ TTS TO BASE64 ------------------

async def tts_to_base64(text: str) -> str:
    """Convert text to speech and return base64 encoded audio"""
    try:
        # Limit text length for TTS
        text = text[:300]
        
        communicate = edge_tts.Communicate(text, TTS_VOICE)
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp = f.name
        
        await communicate.save(tmp)
        
        with open(tmp, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode()
        
        # Clean up temp file
        try:
            os.remove(tmp)
        except:
            pass
        
        return audio_b64
        
    except Exception as e:
        print(f"TTS error: {str(e)}")
        return ""

# ------------------ ACTION HANDLER ------------------

def handle_action(action_json: dict) -> str:
    """Execute an action and return the result"""
    try:
        act = action_json.get("action", "").lower().strip()
        
        print(f"[ACTION] {act}")
        
        if act == "calendar":
            return json.dumps(get_events())
        
        elif act == "email":
            return json.dumps(get_emails())
        
        elif act == "search":
            query = action_json.get("query", "")
            return search_web(query)
        
        elif act in ["browse", "open_website"]:
            url = action_json.get("url", "")
            return browse(url)
        
        elif act == "note_create":
            title = action_json.get("title", "note")
            content = action_json.get("content", "")
            path = create_note(title, content)
            return f"Note saved: {path}"
        
        elif act == "note_list":
            notes = list_notes()
            return json.dumps(notes)
        
        elif act == "note_read":
            title = action_json.get("title", "")
            return read_note(title)
        
        elif act in ["powershell", "run_command"]:
            cmd = action_json.get("cmd") or action_json.get("command", "")
            return run_powershell(cmd)
        
        elif act == "open_app":
            name = action_json.get("name", "").lower().strip()
            
            # Special case for YouTube
            if name == "youtube" or "youtube" in name:
                return browse("https://youtube.com")
            
            return open_app(name)
        
        return "Action not recognized"
        
    except Exception as e:
        print(f"Action error: {str(e)}")
        return f"Error: {str(e)}"

# ------------------ PARSE JSON FROM TEXT ------------------

def extract_json(text: str):
    """Extract JSON object from text"""
    try:
        # Try to find JSON object in the text
        start_idx = text.find('{')
        end_idx = text.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = text[start_idx:end_idx]
            return json.loads(json_str)
    except:
        pass
    
    return None

# ------------------ WEBSOCKET HANDLER ------------------

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    print("[WS] Client connected")
    
    history = []
    
    try:
        while True:
            # Receive message from client
            data = await ws.receive_json()
            user_msg = data.get("text", "").strip()
            deep = data.get("deep", False)
            
            if not user_msg:
                continue
            
            print(f"\n[USER] {user_msg}")
            
            # Save to memory
            save("user", user_msg)
            
            # Get context from memory
            context = recent(10)
            history = [{"role": m["role"], "content": m["content"]} for m in context]
            history.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
            
            # Select model
            model = DEEP_MODEL if deep else FAST_MODEL
            
            # Send thinking state
            await ws.send_json({"type": "thinking"})
            
            # Get AI response
            reply = await ollama_chat(history, model)
            
            # Clean up response
            reply = reply.replace("**", "").strip()
            
            print(f"[REPLY] {reply[:100]}")
            
            # Try to parse as JSON action
            action_data = extract_json(reply)
            
            # If it's an action, execute it and get follow-up response
            if action_data and "action" in action_data:
                print(f"[EXECUTING] {action_data}")
                
                action_result = handle_action(action_data)
                
                # Add to history
                history.append({"role": "assistant", "content": reply})
                history.append({"role": "user", "content": f"Result: {action_result}"})
                
                # Get follow-up response
                reply = await ollama_chat(history, model)
                reply = reply.replace("**", "").strip()
                
                print(f"[FOLLOWUP] {reply[:100]}")
            
            # Save response to memory
            save("assistant", reply)
            
            # Generate speech
            try:
                audio_b64 = await tts_to_base64(reply)
            except:
                audio_b64 = ""
            
            # Send response
            await ws.send_json({
                "type": "response",
                "text": reply,
                "audio": audio_b64
            })
            
    except WebSocketDisconnect:
        print("[WS] Client disconnected")
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except:
            pass

# ------------------ STATIC FILES ------------------

app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")

# For development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)