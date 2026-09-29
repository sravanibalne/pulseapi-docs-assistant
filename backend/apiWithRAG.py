import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState, START

from langgraph_chatbot import call_model

load_dotenv()

# --- Set up retrieval ---

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    dimensions=512,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

vectorstore = PineconeVectorStore(
    index_name="pulseapi-docs",
    embedding=embeddings,
    pinecone_api_key=os.getenv("PINECONE_API_KEY")
)

def retrieve_context(query: str) -> str:
    results = vectorstore.similarity_search(query, k=3)
    chunks = [doc.page_content for doc in results]
    return "\n\n".join(chunks)

# --- Load the prompt template (without the full docs stuffed in) ---

def load_prompt_template():
    with open("pulseapi_system_prompt.txt", "r") as f:
        return f.read()

prompt_template = load_prompt_template()

# --- Build the LangGraph chatbot ---

@st.cache_resource
def build_graph():
    model = ChatAnthropic(
        model="claude-sonnet-4-6",
        temperature=0,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    def call_model(state: MessagesState):
        latest_question = state["messages"][-1].content
        retrieved_chunks = retrieve_context(latest_question)

        system_text = prompt_template.replace("{docs_content}", retrieved_chunks)
        system = SystemMessage(content=system_text)

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