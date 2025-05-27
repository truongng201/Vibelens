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
from langgraph.prebuilt import create_react_agent
from langgraph.graph.message import add_messages


load_dotenv()

pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_host = os.getenv("PINECONE_HOST")
qroq_api_key = os.getenv("GROQ_API_KEY")

pc = Pinecone(
    api_key=pinecone_api_key,
)
index = pc.Index(host = pinecone_host)

@tool
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
    model="llama-3.3-70b-versatile"
)

tools = [get_songs]


# Fix: tool_choice must be a string ("auto" or "none") or a function dict, not a tool dict
agent = create_react_agent(
    model=llm_main.bind_tools(tools, tool_choice="auto"),
    tools=tools
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
                "2. Danh sách các từ khóa chính liên quan đến nội dung, vật thể, cảm xúc, chủ đề hoặc đặc điểm nổi bật trong ảnh, kết hợp với từ khóa từ prompt của người dùng (bắt buộc).\n"
                "Chỉ trả về đúng hai mục trên, trình bày bằng tiếng Việt, không thêm giải thích, không lặp lại yêu cầu, không bổ sung thông tin ngoài hai mục trên."
            )
        },
        {"role": "user", "content": last_message.content}
    ])
    
    print(f"Image to text model: {result.content}")
    
    state["messages"].append(result)
    return state

def recommendation(state: State):
    last_message = state["messages"][-1]
    # Compose the system and user messages for the agent
    system_message = {
        "role": "system",
        "content": (
            "Bạn nhận được danh sách từ khóa mô tả nội dung, cảm xúc và chủ đề của bức ảnh, cùng với prompt từ người dùng. "
            "Bạn có quyền sử dụng công cụ get_songs để tìm kiếm các bài hát phù hợp nhất từ cơ sở dữ liệu vector, dựa trên mức độ tương đồng với các từ khóa và thông tin đã cung cấp. "
            "Hãy gọi get_songs với các từ khóa và prompt, sau đó trả về danh sách tối đa 5 bài hát phù hợp nhất, kèm theo tên bài hát, tác giả và một đoạn trích ngắn (snippet) của lời nhạc phù hợp nhất với từ khóa. "
            "Chỉ trình bày kết quả dưới dạng danh sách đánh số (1, 2, 3...), không giải thích, không thêm thông tin ngoài tên, tác giả và đoạn trích lời nhạc."
        )
    }
    user_message = {
        "role": "user",
        "content": last_message["content"] if isinstance(last_message, dict) and "content" in last_message else str(last_message)
    }
    # Call the agent with the correct message format
    result = agent.invoke({
        "messages": [system_message, user_message]
    })
        
    # Append the result to the message history and return the updated state
    state["messages"].append(result["messages"][-1] if isinstance(result, dict) and "messages" in result else result)
    
    return state

graph_builder = StateGraph(State)
graph_builder.add_node("image2text", img2text)
graph_builder.add_node("recommendation", recommendation)
graph_builder.add_edge(START, "image2text")
graph_builder.add_edge("image2text", "recommendation")
graph_builder.add_edge("recommendation", END)

graph = graph_builder.compile()
user_prompt = input("Enter the prompt: ")
image_url = input("Enter the url: ")
state = graph.invoke({"messages": [{"role": "user", "content": f"{user_prompt}: {image_url}"}]})

print(f"Final result: {state['messages'][-1].content}")


