import os
import streamlit as st
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState, START

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
    return builder.compile(checkpointer=checkpointer)

graph = build_graph()

# --- Streamlit UI ---

st.title("PulseAPI Docs Assistant (RAG-powered)")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_input = st.chat_input("Ask a question about PulseAPI...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    config = {"configurable": {"thread_id": "streamlit-session"}}
    result = graph.invoke({"messages": [{"role": "user", "content": user_input}]}, config)
    assistant_reply = result["messages"][-1].content

    with st.chat_message("assistant"):
        st.write(assistant_reply)
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})