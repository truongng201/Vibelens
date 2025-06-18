import re, math, random
from transformers import pipeline
from googletrans import Translator
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer, util
import os

class AgentRecommender:
    def __init__(self, ):
        self.pinecone_api_key = os.getenv('PINECONE_API_KEY')
        self.pinecone_host = os.getenv('PINECONE_HOST')
        self.captioner = pipeline("image-to-text", model="nlpconnect/vit-gpt2-image-captioning")
        self.translator = Translator()
        self.pinecone = Pinecone(api_key=self.pinecone_api_key)
        self.index = self.pinecone.Index(host=self.pinecone_host)
        # self.model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v2')

    def split_by_capital_letter(self, text):
        return [s.strip() for s in re.findall(r'(?:[A-Z][^A-Z]*)', text) if s.strip()]

    def translate_dual(self, prompt):
        result = self.translator.translate(prompt, dest='vi')
        src_lang = result.src  # Google đoán ngôn ngữ gốc

        vi_prompt = result.text
        en_prompt = prompt if src_lang == 'en' else self.translator.translate(prompt, dest='en').text

        return en_prompt, vi_prompt

    def process_hits(self, hits, lang='en'):
        recommendations = []
        for idx, hit in enumerate(hits):
            full_text = hit['fields']['text']
            lyrics_match = re.search(r'Lyrics:\s*(.*)', full_text, re.DOTALL | re.IGNORECASE)
            lyrics = lyrics_match.group(1).strip() if lyrics_match else ""

            # segments = self.split_by_capital_letter(lyrics)
            # if not segments:
            #     continue

            # segment_embs = self.model.encode(segments, convert_to_tensor=True)
            # sim_scores = util.cos_sim(caption_emb, segment_embs)[0].tolist()

            # best_idx = max(range(len(sim_scores)), key=lambda i: sim_scores[i])
            # best_segment = segments[best_idx]
            # best_score = round(sim_scores[best_idx], 3)
            seed = random.randint(1, 10000)
            first_line = full_text.split('.')[0]
            title, artist = (first_line.split(' by ', 1) + ["Unknown"])[:2]

            segment_start = random.randint(10, 60)
            segment_end = segment_start + random.randint(10, 30)
            duration = random.randint(150, 240)

            recommendations.append({
                "id": hit['_id'],
                "title": title.strip(),
                "artist": artist.strip(),
                "image_url":f"https://picsum.photos/seed/{title.strip()}-{seed}/64/64",
                "segment": {
                    "start": segment_start,
                    "end": segment_end,
                    "description": lyrics[:100] + "...",
                    "relevanceScore": round(math.tanh(3*hit['_score']),4)*100,
                },
                "duration": duration,
            })

        return sorted(recommendations, key=lambda x: x['segment']['relevanceScore'], reverse=True)

    def recommend_from_image(self, url, user_prompt=None):
        # Step 1: Caption and translate
        en_caption = self.captioner(url)[0]['generated_text']
        vi_caption = self.translator.translate(en_caption, src='en', dest='vi').text
        # print(f"English Caption: {en_caption}")
        # print(f"Vietnamese Caption: {vi_caption}")

        if user_prompt:
            en_user_caption, vi_user_caption = self.translate_dual(user_prompt)
            en_caption += ". " + en_user_caption
            vi_caption += ". " + vi_user_caption

        # Step 2: Encode
        # en_caption_emb = self.model.encode(en_caption, convert_to_tensor=True)
        # vi_caption_emb = self.model.encode(vi_caption, convert_to_tensor=True)

        # Step 3: Query Pinecone
        vi_query_payload = {"inputs": {"text": vi_caption}, "top_k": 5}
        en_query_payload = {"inputs": {"text": en_caption}, "top_k": 5}

        vi_hits = self.index.search(namespace="__default__", query=vi_query_payload)['result']['hits']
        en_hits = self.index.search(namespace="__default__", query=en_query_payload)['result']['hits']

        # Step 4: Process and combine
        recommendations_en = self.process_hits(en_hits, lang='en')
        recommendations_vi = self.process_hits(vi_hits, lang='vi')
        unique_ids = set()
        combined = []

        for rec in recommendations_en + recommendations_vi:
            if rec["id"] not in unique_ids:
                unique_ids.add(rec["id"])
                combined.append(rec)

        combined = sorted(combined, key=lambda x: x['segment']['relevanceScore'], reverse=True)

        
        return combined
