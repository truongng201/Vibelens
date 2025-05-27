import os
from dotenv import load_dotenv
from typing import Annotated, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from pinecone import Pinecone
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langgraph.graph.message import add_messages
from langchain.agents import initialize_agent, AgentType


load_dotenv()

pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_host = os.getenv("PINECONE_HOST")
qroq_api_key = os.getenv("GROQ_API_KEY")

pc = Pinecone(
    api_key=pinecone_api_key,
)
index = pc.Index(host = pinecone_host)

def get_songs(context: str) -> dict:
    """
    Retrieve the top 5 most relevant songs as well as their lyrics for a given context using a vector search.

    Args:
        context (str): A short description of the desired mood, vibe, or situation 
                       (e.g., "a calm evening beach walk").

    Returns:
        dict: A dictionary with a 'result' key containing a 'hits' list.
              Each hit includes:
                - '_id': the song ID
                - '_score': similarity score
                - 'fields': a dictionary containing:
                    - 'category': song genre or style
                    - 'text': full description including title, artist, genre, and lyrics
    """
    query_payload = {
        "inputs": {"text": context},
        "top_k": 5
    }
    
    results = index.search(namespace="", query=query_payload)
    return results

llm_vision = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct"
)

llm_main = ChatGroq(
    model="llama-3.3-70b-versatile",
    tool=[get_songs]
)

class State(TypedDict):
    messages: Annotated[list, add_messages]
    
def img2text(state: State):
    last_message = state["messages"][-1]
    
    result = llm_vision.invoke([
        {
            "role": "system",
            "content": (
                "Bạn là một trợ lý AI chuyên phân tích hình ảnh. "
                "Nhiệm vụ của bạn là quan sát kỹ bức ảnh và prompt của người dùng, sau đó trả lời thật ngắn gọn, súc tích, rõ ràng, chỉ gồm hai phần:\n"
                "1. Mô tả tổng quan bối cảnh bức ảnh (không quá 2 câu, tập trung vào không gian, thời gian, hoạt động chính hoặc cảm xúc chung).\n"
                "2. Danh sách các từ khóa chính liên quan đến nội dung, vật thể, cảm xúc, chủ đề hoặc đặc điểm nổi bật trong ảnh, kết hợp với từ khóa từ prompt của người dùng.\n"
                "Chỉ trả về đúng hai mục trên, trình bày bằng tiếng Việt, không thêm giải thích, không lặp lại yêu cầu, không bổ sung thông tin ngoài hai mục trên."
            )
        },
        {"role": "user", "content": last_message.content}
    ])
    
    return {"messages": [result]}

graph_builder = StateGraph(State)
graph_builder.add_node("image2text", img2text)
graph_builder.add_edge(START, "image2text")
graph_builder.add_edge("image2text", END)

graph = graph_builder.compile()
user_prompt = input("Enter the prompt: ")
image_url = input("Enter the url: ")
state = graph.invoke({"messages": [{"role": "user", "content": f"{user_prompt}: {image_url}"}]})

print(state["messages"][-1].content)


