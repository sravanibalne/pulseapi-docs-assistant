import os
import streamlit as st
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState, START

load_dotenv()

# --- Load the docs content and system prompt template from disk ---

def load_system_prompt():
    with open("pulseapi_docs.md", "r") as f:
        docs_content = f.read()

    with open("pulseapi_system_prompt.txt", "r") as f:
        prompt_template = f.read()

    return prompt_template.replace("{docs_content}", docs_content)

# --- Build the LangGraph chatbot ---

@st.cache_resource
def build_graph():
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
    return builder.compile(checkpointer=checkpointer)

graph = build_graph()

# --- Streamlit UI ---

st.title("PulseAPI Docs Assistant")

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