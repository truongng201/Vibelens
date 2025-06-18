import os
from typing import List, Dict, Any
from pinecone import Pinecone
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq


class AgentRecommender:
    def __init__(self):
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_host = os.getenv("PINECONE_HOST")
        self.groq_api_key = os.getenv("GROQ_API_KEY")

        self.pc = Pinecone(api_key=self.pinecone_api_key)
        self.index = self.pc.Index(host=self.pinecone_host)

        self.llm_vision = ChatGroq(
            model="meta-llama/llama-4-scout-17b-16e-instruct"
        )
        self.llm_main = ChatGroq(
            model="llama-3.3-70b-versatile"
        )

        self.tools = [self.get_songs]
        self.agent = create_react_agent(
            model=self.llm_main.bind_tools(self.tools, tool_choice="auto"),
            tools=self.tools
        )

    @tool
    def get_songs(self, context: str) -> dict:
        query_payload = {
            "inputs": {"text": context},
            "top_k": 5
        }
        results = self.index.search(namespace="__default__", query=query_payload)
        return results

    def img2text(self, image_url: str, user_prompt: str) -> str:
        result = self.llm_vision.invoke([
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
            {"role": "user", "content": f"{user_prompt}: {image_url}"}
        ])
        return result.content

    def recommend(self, context: str) -> List[Dict[str, Any]]:
        # Use the agent to get song recommendations
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
            "content": context
        }
        result = self.agent.invoke({"messages": [system_message, user_message]})
        # Parse the result to extract song info
        songs = []
        if isinstance(result, dict) and "messages" in result:
            content = result["messages"][-1].get("content", "")
        else:
            content = getattr(result, "content", "")
        # Example parsing, adjust as needed based on actual output format
        for line in content.split('\n'):
            if line.strip() and line[0].isdigit():
                # Example: "1. Song Title - Author: snippet"
                parts = line.split('.', 1)[-1].strip().split('-', 1)
                if len(parts) == 2:
                    title_author, snippet = parts
                    title, author = title_author.split('by') if 'by' in title_author else (title_author, "")
                    songs.append({
                        "title": title.strip(),
                        "author": author.strip(),
                        "description": snippet.strip(),
                        "segment_song": snippet.strip(),
                        "match_score": None  # Fill if available from Pinecone results
                    })
        return songs

    def recommend_from_image(self, image_url: str, user_prompt: str) -> List[Dict[str, Any]]:
        context = self.img2text(image_url, user_prompt)
        return self.recommend(context)