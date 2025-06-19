import os

class TextEmbedderTool:
    def __init__(self):
        model_path = os.path.abspath(
        )
        self.embedder = text.TextEmbedder.create_from_file(model_path)

    def embed(self, text_input: str):
        result = self.embedder.embed(text_input)
        return result.embeddings[0].feature_vector

    def similarity(self, v1, v2) -> float:
        return self.embedder.cosine_similarity(v1, v2)

if __name__ == "__main__":
    tool = TextEmbedderTool()
    v1 = tool.embed("machine learning")
    v2 = tool.embed("artificial intelligence")
    print("Cosine similarity:", tool.similarity(v1, v2))
