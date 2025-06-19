import contextlib
import io
import logging
import os
import shutil
import uuid
from typing import Any, Dict, List, Optional

# from chromadb.api import ClientAPI # TODO: Remove chromadb

from crewai.memory.storage.base_rag_storage import BaseRAGStorage
from crewai.utilities import EmbeddingConfigurator
from crewai.utilities.constants import MAX_FILE_NAME_LENGTH
from crewai.utilities.paths import db_storage_path


@contextlib.contextmanager
def suppress_logging(
    logger_name="chromadb.segment.impl.vector.local_persistent_hnsw", # TODO: Update logger_name
    level=logging.ERROR,
):
    logger = logging.getLogger(logger_name)
    original_level = logger.getEffectiveLevel()
    logger.setLevel(level)
    with (
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
        contextlib.suppress(UserWarning),
    ):
        yield
    logger.setLevel(original_level)


class RAGStorage(BaseRAGStorage):
    """
    Extends Storage to handle embeddings for memory entries, improving
    search efficiency.
    """

    app: Any | None = None # TODO: Replace ClientAPI with a suitable type

    def __init__(
        self, type, allow_reset=True, embedder_config=None, crew=None, path=None
    ):
        super().__init__(type, allow_reset, embedder_config, crew)
        agents = crew.agents if crew else []
        agents = [self._sanitize_role(agent.role) for agent in agents]
        agents = "_".join(agents)
        self.agents = agents
        self.storage_file_name = self._build_storage_file_name(type, agents)

        self.type = type

        self.allow_reset = allow_reset
        self.path = path
        self._initialize_app()

    def _set_embedder_config(self):
        configurator = EmbeddingConfigurator()
        self.embedder_config = configurator.configure_embedder(self.embedder_config)

    def _initialize_app(self):
        import chromadb
        from chromadb.config import Settings

        self._set_embedder_config()
        # import chromadb # TODO: Remove chromadb
        # from chromadb.config import Settings # TODO: Remove chromadb

        # self._set_embedder_config() # TODO: Remove chromadb
        # chroma_client = chromadb.PersistentClient( # TODO: Remove chromadb
        #     path=self.path if self.path else self.storage_file_name,
        #     settings=Settings(allow_reset=self.allow_reset),
        # )

        # self.app = chroma_client # TODO: Remove chromadb

        # try: # TODO: Remove chromadb
        #     self.collection = self.app.get_collection(
        #         name=self.type, embedding_function=self.embedder_config
        #     )
        # except Exception: # TODO: Remove chromadb
        #     self.collection = self.app.create_collection(
        #         name=self.type, embedding_function=self.embedder_config
        #     )
        raise NotImplementedError("ChromaDB RAG storage is no longer supported.")

    def _sanitize_role(self, role: str) -> str:
        """
        Sanitizes agent roles to ensure valid directory names.
        """
        return role.replace("\n", "").replace(" ", "_").replace("/", "_")

    def _build_storage_file_name(self, type: str, file_name: str) -> str:
        """
        Ensures file name does not exceed max allowed by OS
        """
        base_path = f"{db_storage_path()}/{type}"

        if len(file_name) > MAX_FILE_NAME_LENGTH:
            logging.warning(
                f"Trimming file name from {len(file_name)} to {MAX_FILE_NAME_LENGTH} characters."
            )
            file_name = file_name[:MAX_FILE_NAME_LENGTH]

        return f"{base_path}/{file_name}"

    def save(self, value: Any, metadata: Dict[str, Any]) -> None:
        # if not hasattr(self, "app") or not hasattr(self, "collection"): # TODO: Remove chromadb
        #     self._initialize_app()
        # try: # TODO: Remove chromadb
        #     self._generate_embedding(value, metadata)
        # except Exception as e: # TODO: Remove chromadb
        #     logging.error(f"Error during {self.type} save: {str(e)}")
        raise NotImplementedError("ChromaDB RAG storage is no longer supported.")

    def search(
        self,
        query: str,
        limit: int = 3,
        filter: Optional[dict] = None,
        score_threshold: float = 0.35,
    ) -> List[Any]:
        # if not hasattr(self, "app"): # TODO: Remove chromadb
        #     self._initialize_app()

        # try: # TODO: Remove chromadb
        #     with suppress_logging():
        #         response = self.collection.query(query_texts=query, n_results=limit)

        #     results = []
        #     for i in range(len(response["ids"][0])): # TODO: Remove chromadb
        #         result = {
        #             "id": response["ids"][0][i],
        #             "metadata": response["metadatas"][0][i],
        #             "context": response["documents"][0][i],
        #             "score": response["distances"][0][i],
        #         }
        #         if result["score"] >= score_threshold: # TODO: Remove chromadb
        #             results.append(result)

        #     return results
        # except Exception as e: # TODO: Remove chromadb
        #     logging.error(f"Error during {self.type} search: {str(e)}")
        #     return []
        raise NotImplementedError("ChromaDB RAG storage is no longer supported.")

    def _generate_embedding(self, text: str, metadata: Dict[str, Any]) -> None:  # type: ignore
        # if not hasattr(self, "app") or not hasattr(self, "collection"): # TODO: Remove chromadb
        #     self._initialize_app()

        # self.collection.add( # TODO: Remove chromadb
        #     documents=[text],
        #     metadatas=[metadata or {}],
        #     ids=[str(uuid.uuid4())],
        # )
        raise NotImplementedError("ChromaDB RAG storage is no longer supported.")

    def reset(self) -> None:
        try:
            if self.app:
                # self.app.reset() # TODO: Remove chromadb
                shutil.rmtree(f"{db_storage_path()}/{self.type}")
                self.app = None
                # self.collection = None # TODO: Remove chromadb
        except Exception as e:
            if "attempt to write a readonly database" in str(e): # TODO: Remove chromadb
                # Ignore this specific error
                pass
            else:
                raise Exception(
                    f"An error occurred while resetting the {self.type} memory: {e}"
                )
        raise NotImplementedError("ChromaDB RAG storage is no longer supported.")

    def _create_default_embedding_function(self):
        # from chromadb.utils.embedding_functions.openai_embedding_function import ( # TODO: Remove chromadb
        #     OpenAIEmbeddingFunction,
        # )

        # return OpenAIEmbeddingFunction( # TODO: Remove chromadb
        #     api_key=os.getenv("OPENAI_API_KEY"), model_name="text-embedding-3-small"
        # )
        raise NotImplementedError("ChromaDB RAG storage is no longer supported.")
