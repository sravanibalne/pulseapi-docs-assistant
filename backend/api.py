import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState, START

load_dotenv()

# --- Same chatbot-building logic as app.py ---

def load_system_prompt():
    with open("pulseapi_docs.md", "r") as f:
        docs_content = f.read()
    with open("pulseapi_system_prompt.txt", "r") as f:
        prompt_template = f.read()
    return prompt_template.replace("{docs_content}", docs_content)

model = ChatAnthropic(
    model="claude-sonnet-4-6",
    temperature=0,
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
)

system_prompt_text = load_system_prompt()

def call_model(state: MessagesState):
    system = SystemMessage(content=system_prompt_text)
    response = model.invoke([system] + state["messages"])
    return {"messages": response}

builder = StateGraph(MessagesState)
builder.add_node("call_model", call_model)
builder.add_edge(START, "call_model")

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# --- FastAPI app ---

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    thread_id: str

class ChatResponse(BaseModel):
    reply: str

@app.post("/chat", response_model=ChatResponse)
def handle_message(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    result = graph.invoke({"messages": [{"role": "user", "content": request.message}]}, config)
    reply = result["messages"][-1].content
    return ChatResponse(reply=reply)