# 🎵 Vibelens: Image-based Music Recommendation

Vibelens is an AI-powered system that recommends the most relevant segment of a song based on an uploaded image. Leveraging the latest in computer vision, large language models, and music content analysis, Vibelens transforms visual emotion into musical resonance.

---

## 📄 Brief Description

**Vibelens** allows users to upload an image and receive a curated snippet of a song that emotionally or thematically matches the content of that image. This is not just about recommending an entire song — we identify the *exact part* (e.g., chorus, bridge, verse) of the song that best matches the mood, setting, or context of the uploaded image. The project integrates image captioning (im2txt), vector search, and song lyric analysis to achieve this level of precision.

---

## 🎯 Functional & Non-functional Requirements

### ✅ Functional Requirements

- User uploads an image through the frontend interface.
- Image is captioned via `im2txt` to extract semantic meaning.
- Captions are embedded and stored in **Pinecone** for similarity search.
- Lyrics of songs are scraped and embedded using the same method.
- The system retrieves the most semantically aligned song *segment*.
- Users are shown a player with the highlighted part of the song.

### 🚫 Non-functional Requirements

- Scalable backend (using Celery, Redis, PostgreSQL).
- Near real-time response time (under 3 seconds for recommendation).
- Maintainability: Modular design with isolated crawling, captioning, and recommendation services.
- Observability and monitoring with logging and retries via Celery.
- Educational use of Kafka for simulating a streaming pipeline.

---

## 🔧 Tech Stack

| Layer                     | Technology                                          |
|---------------------------|-----------------------------------------------------|
| Frontend                  | Next.js                                             |
| Backend                   | Flask, Celery as worker                             |
| Crawler                   | Scrapy (with Celery, Redis, and Scheduler)          |
| Image Captioning          | `im2txt`, powered by VIT-GPT2-IMAGE-CAPTIONING      |
| Vector Search             | Pinecone                                            |            
| NLP & Music Matching      | Transformer `distiluse-base-multilingual-cased-v2`  |
| Database                  | PostgreSQL                                          |
| Streaming                 | Kafka (for educational purposes)                    |
| Task Queue                | Celery + Redis                                      |
| Music & Lyrics Processing | Celery worker (downloads mp3, scrapes lyrics)       |
| Deployment                | Docker/Docker Swarm/Digital Ocean/Github Action     |

### Example LLM Configuration

```python
llm = ChatGroq(
    model="llama-3.2-90b-vision-preview",
    temperature=0.6,
    max_retries=2,
    api_key=qroq_api_key
)

chain = LLMChain(
    llm=llm,
    prompt=prompt,
    verbose=True
)
```

---

## 👥 Team Members and Roles

| Name                | Role                                |
|---------------------|-------------------------------------|
| Nguyen Xuan Truong  | DevOps Engineer / Project Lead      |
| Nguyen Tien Nhan    | Data Engineer                       |
| Le Mai Thanh Son    | Backend Developer                   |
| Nguyen Son Giang    | Algorithm Specialist                |
| Nguyen Dai An       | ML/NLP Specialist                   |

---

## 📅 Timeline (Planned Milestones)

| Week | Milestone |
|------|-----------|
| Week 1 | Project Setup & Initial Research |
| Week 2 | Build Image Upload + Captioning System |
| Week 3 | Implement Lyrics Scraper & Audio Segmenting |
| Week 4 | Vector Search Setup with Qdrant |
| Week 5 | Integrate LLM & Recommendation Chain |
| Week 6 | Build Frontend UI (Next.js) |
| Week 7 | Integrate Audio Player with Highlighting |
| Week 8 | Deploy Backend Services + Load Testing |
| Week 9 | Final Bug Fixes + Documentation |
| Week 10 | Demo & Presentation |
