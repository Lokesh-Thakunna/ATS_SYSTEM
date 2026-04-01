from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)
model = None

def get_model():
    global model
    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")
    return model


def generate_embedding(text):
    """
    Generate embedding for text. Returns None for empty/invalid text.
    """
    if not text or not text.strip():
        return None

    try:
        model = get_model()
        embedding = model.encode(text.strip())

        # Convert to list and validate
        if hasattr(embedding, "tolist"):
            embedding = embedding.tolist()

        # Ensure it's not empty and has proper dimensions
        if not embedding or len(embedding) == 0:
            logger.warning(f"Generated empty embedding for text: {text[:50]}...")
            return None

        return embedding

    except Exception as e:
        logger.error(f"Embedding generation failed for text: {text[:50]}... Error: {str(e)}")
        return None