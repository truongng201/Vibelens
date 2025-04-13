from sentence_transformers import SentenceTransformer

_model_instance = None

def get_model():
    global _model_instance
    if _model_instance is None:
        model_name = "all-MiniLM-L6-v2"
        if _model_instance is not None:
            print(f"✅ Model '{model_name}' already loaded.")
            return _model_instance
        print(f"🔵 Loading sentence transformer model {model_name}...")
        _model_instance = SentenceTransformer(model_name)
        print("✅ Model loaded.")
    return _model_instance