import os
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document

load_dotenv()

# 1. Load the raw docs text
with open("pulseapi_docs.md", "r") as f:
    raw_text = f.read()

# 2. Split into chunks
splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50
)
chunks = splitter.split_text(raw_text)

print(f"Split into {len(chunks)} chunks.")

# 3. Wrap each chunk as a Document object (LangChain's standard text container)
documents = [Document(page_content=chunk) for chunk in chunks]

# 4. Set up the embeddings model (512 dimensions, matching our Pinecone index)
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    dimensions=512,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# 5. Embed and upload all chunks to Pinecone in one call
vectorstore = PineconeVectorStore.from_documents(
    documents=documents,
    embedding=embeddings,
    index_name="pulseapi-docs",
    pinecone_api_key=os.getenv("PINECONE_API_KEY")
)

print("Done — all chunks embedded and stored in Pinecone.")