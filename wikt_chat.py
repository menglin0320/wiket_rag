"""
This script is a Streamlit application that 
allows users to ask questions about HEMA (Historical European Martial Arts).
It uses a vector database (VDB) to retrieve relevant information based on user 
queries. The application is designed to provide a chat-like interface for 
interaction.
"""
import streamlit as st
import os
import json
from dotenv import load_dotenv

from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage, Document
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.chat_engine.condense_question import CondenseQuestionChatEngine
from src.prompts import condense_question_prompt, response_prompt

@st.cache_resource(show_spinner="Loading vector index...")
def load_vdb(json_data_path, 
             storage_path):
    """
    Loads a vector database (VDB) from the specified storage path if it exists.
    If the storage path does not exist, it creates a new VDB from the provided JSON data.

    The JSON data is expected to be a list of chunks, where each chunk is a dictionary
    containing fields such as 'title', 'url', 'type', 'text', and 'n_images'.

    Args:
        json_data_path (str): Path to the JSON file containing the data chunks.
        storage_path (str): Path to the directory where the vector database is stored.

    Returns:
        VectorStoreIndex: The loaded or newly created vector database index.
    """
    if os.path.exists(storage_path):
        storage_context = StorageContext.from_defaults(persist_dir=storage_path)
        index = load_index_from_storage(storage_context)
        return index
    else:
        with open(json_data_path, 'r') as f:
            raw_chunks = json.load(f)
        
        # Convert each chunk into a Document object
        documents = [
        Document(text=f"Title: {chunk.get('title', '')}\nURL: {chunk.get('url', '')}\nType: {chunk.get('type', '')}\n\n{chunk['text']}", metadata={"title": chunk.get("title", ""), 
                                                "url": chunk.get("url", ""),
                                                "type": chunk.get("type", ""),
                                                "n_images": chunk.get("n_images", "")})
            for chunk in raw_chunks 
        ]
        
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=storage_path)
        return index

if __name__ == "__main__":
    chunk_data_path = "data/wikt_chunks.json"
    # Load environment variables
    load_dotenv()
    # Set up LLM and service context
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0001)
    # Define storage path
    storage_path = "./vectorstore"
    index = load_vdb(chunk_data_path, storage_path)
    # Set up Streamlit app
    st.title("ask questions about hema!!!")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Ask questions about hema!!!"}
        ]

    query_engine = index.as_query_engine(
        text_qa_template=response_prompt,
        similarity_top_k=5,
        verbose=True
    )

    chat_engine = CondenseQuestionChatEngine.from_defaults(
        query_engine=query_engine,
        condense_question_prompt=condense_question_prompt,
        verbose=True,
        similarity_top_k=5,
        memory=ChatMemoryBuffer(token_limit=1500)
    )

    # Display message history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    history = [
        ChatMessage(
            role=MessageRole.USER if m["role"]=="user" else MessageRole.ASSISTANT,
            content=m["content"]
        )
        for m in st.session_state.messages
    ]
    # Handle user input
    if prompt := st.chat_input("Your question"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = chat_engine.chat(prompt, chat_history=history)

                st.write(response.response)
                st.session_state.pending_user_message = prompt
                    
                response_str = '\n'.join([response.response])
                st.session_state.messages.append({"role": "assistant", "content": response_str})
            
