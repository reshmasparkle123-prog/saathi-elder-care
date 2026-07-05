import os,time,hashlib
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
app=FastAPI()
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["POST"],allow_headers=["*"])
client=Groq(api_key=os.environ.get("GROQ_API_KEY"))
SYSTEM="You are Saathi, warm AI elder care companion. Speak Hinglish. 2-3 sentences max."
_cache={}
class ChatRequest(BaseModel):
 user_id:str
 message:str
def _h(t): return hashlib.md5(t.strip().lower().encode()).hexdigest()
@app.post("/chat")
async def chat(req:ChatRequest):
 k=_h(req.message)
 if k in _cache and time.time()-_cache[k][1]<3600: return {"response":_cache[k][0]}
 try:
  c=client.chat.completions.create(model="llama-3.3-70b-versatile",messages=[{"role":"system","content":SYSTEM},{"role":"user","content":req.message}],max_tokens=200)
  r=c.choices[0].message.content.strip()
  _cache[k]=(r,time.time())
  return {"response":r}
 except Exception as e: raise HTTPException(status_code=500,detail=str(e))
@app.get("/health")
def health(): return {"status":"ok"}
if __name__=="__main__":
 import uvicorn
 uvicorn.run(app,host="0.0.0.0",port=int(os.environ.get("PORT",8001)))
