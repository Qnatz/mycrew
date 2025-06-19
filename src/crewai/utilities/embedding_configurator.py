import os
from typing import Any, Dict, Optional, cast

# from chromadb import Documents, EmbeddingFunction, Embeddings # TODO: Remove chromadb
# from chromadb.api.types import validate_embedding_function # TODO: Remove chromadb


class EmbeddingConfigurator:
    def __init__(self):
        self.embedding_functions = {
            "openai": self._configure_openai,
            "azure": self._configure_azure,
            "ollama": self._configure_ollama,
            "vertexai": self._configure_vertexai,
            "google": self._configure_google,
            "cohere": self._configure_cohere,
            "voyageai": self._configure_voyageai,
            "bedrock": self._configure_bedrock,
            "huggingface": self._configure_huggingface,
            "watson": self._configure_watson,
            "custom": self._configure_custom,
        }

    def configure_embedder(
        self,
        embedder_config: Optional[Dict[str, Any]] = None,
    ) -> Any: # TODO: Replace EmbeddingFunction with a suitable type
        """Configures and returns an embedding function based on the provided config."""
        if embedder_config is None:
            return self._create_default_embedding_function()

        provider = embedder_config.get("provider")
        config = embedder_config.get("config", {})
        model_name = config.get("model") if provider != "custom" else None

        if provider not in self.embedding_functions:
            raise Exception(
                f"Unsupported embedding provider: {provider}, supported providers: {list(self.embedding_functions.keys())}"
            )

        embedding_function = self.embedding_functions[provider]
        return (
            embedding_function(config)
            if provider == "custom"
            else embedding_function(config, model_name)
        )

    @staticmethod
    def _create_default_embedding_function():
        # from chromadb.utils.embedding_functions.openai_embedding_function import ( # TODO: Remove chromadb
        #     OpenAIEmbeddingFunction,
        # )

        # return OpenAIEmbeddingFunction( # TODO: Remove chromadb
        #     api_key=os.getenv("OPENAI_API_KEY"), model_name="text-embedding-3-small"
        # )
        raise NotImplementedError("ChromaDB embedding functions are no longer supported.")

    @staticmethod
    def _configure_openai(config, model_name):
        # from chromadb.utils.embedding_functions.openai_embedding_function import ( # TODO: Remove chromadb
        #     OpenAIEmbeddingFunction,
        # )

        # return OpenAIEmbeddingFunction( # TODO: Remove chromadb
        #     api_key=config.get("api_key") or os.getenv("OPENAI_API_KEY"),
        #     model_name=model_name,
            # api_base=config.get("api_base", None), # TODO: Remove chromadb
            # api_type=config.get("api_type", None), # TODO: Remove chromadb
            # api_version=config.get("api_version", None), # TODO: Remove chromadb
            # default_headers=config.get("default_headers", None), # TODO: Remove chromadb
            # dimensions=config.get("dimensions", None), # TODO: Remove chromadb
            # deployment_id=config.get("deployment_id", None), # TODO: Remove chromadb
            # organization_id=config.get("organization_id", None), # TODO: Remove chromadb
        # )
        raise NotImplementedError("ChromaDB embedding functions are no longer supported.")

    @staticmethod
    def _configure_azure(config, model_name):
        # from chromadb.utils.embedding_functions.openai_embedding_function import ( # TODO: Remove chromadb
        #     OpenAIEmbeddingFunction,
        # )

        # return OpenAIEmbeddingFunction( # TODO: Remove chromadb
        #     api_key=config.get("api_key"),
        #     api_base=config.get("api_base"),
        #     api_type=config.get("api_type", "azure"),
        #     api_version=config.get("api_version"),
        #     model_name=model_name,
        #     default_headers=config.get("default_headers"),
        #     dimensions=config.get("dimensions"),
        #     deployment_id=config.get("deployment_id"),
        #     organization_id=config.get("organization_id"),
        # )
        raise NotImplementedError("ChromaDB embedding functions are no longer supported.")

    @staticmethod
    def _configure_ollama(config, model_name):
        # from chromadb.utils.embedding_functions.ollama_embedding_function import ( # TODO: Remove chromadb
        #     OllamaEmbeddingFunction,
        # )

        # return OllamaEmbeddingFunction( # TODO: Remove chromadb
        #     url=config.get("url", "http://localhost:11434/api/embeddings"),
        #     model_name=model_name,
        # )
        raise NotImplementedError("ChromaDB embedding functions are no longer supported.")

    @staticmethod
    def _configure_vertexai(config, model_name):
        # from chromadb.utils.embedding_functions.google_embedding_function import ( # TODO: Remove chromadb
        #     GoogleVertexEmbeddingFunction,
        # )

        # return GoogleVertexEmbeddingFunction( # TODO: Remove chromadb
        #     model_name=model_name,
        #     api_key=config.get("api_key"),
        #     project_id=config.get("project_id"),
        #     region=config.get("region"),
        # )
        raise NotImplementedError("ChromaDB embedding functions are no longer supported.")

    @staticmethod
    def _configure_google(config, model_name):
        # from chromadb.utils.embedding_functions.google_embedding_function import ( # TODO: Remove chromadb
        #     GoogleGenerativeAiEmbeddingFunction,
        # )

        # return GoogleGenerativeAiEmbeddingFunction( # TODO: Remove chromadb
        #     model_name=model_name,
        #     api_key=config.get("api_key"),
        #     task_type=config.get("task_type"),
        # )
        raise NotImplementedError("ChromaDB embedding functions are no longer supported.")

    @staticmethod
    def _configure_cohere(config, model_name):
        # from chromadb.utils.embedding_functions.cohere_embedding_function import ( # TODO: Remove chromadb
        #     CohereEmbeddingFunction,
        # )

        # return CohereEmbeddingFunction( # TODO: Remove chromadb
        #     model_name=model_name,
        #     api_key=config.get("api_key"),
        # )
        raise NotImplementedError("ChromaDB embedding functions are no longer supported.")

    @staticmethod
    def _configure_voyageai(config, model_name):
        # from chromadb.utils.embedding_functions.voyageai_embedding_function import ( # TODO: Remove chromadb
        #     VoyageAIEmbeddingFunction,
        # )

        # return VoyageAIEmbeddingFunction( # TODO: Remove chromadb
        #     model_name=model_name,
        #     api_key=config.get("api_key"),
        # )
        raise NotImplementedError("ChromaDB embedding functions are no longer supported.")

    @staticmethod
    def _configure_bedrock(config, model_name):
        # from chromadb.utils.embedding_functions.amazon_bedrock_embedding_function import ( # TODO: Remove chromadb
        #     AmazonBedrockEmbeddingFunction,
        # )

        # # Allow custom model_name override with backwards compatibility # TODO: Remove chromadb
        # kwargs = {"session": config.get("session")}
        # if model_name is not None:
        #     kwargs["model_name"] = model_name
        # return AmazonBedrockEmbeddingFunction(**kwargs)
        raise NotImplementedError("ChromaDB embedding functions are no longer supported.")

    @staticmethod
    def _configure_huggingface(config, model_name):
        # from chromadb.utils.embedding_functions.huggingface_embedding_function import ( # TODO: Remove chromadb
        #     HuggingFaceEmbeddingServer,
        # )

        # return HuggingFaceEmbeddingServer( # TODO: Remove chromadb
        #     url=config.get("api_url"),
        # )
        raise NotImplementedError("ChromaDB embedding functions are no longer supported.")

    @staticmethod
    def _configure_watson(config, model_name):
        try:
            import ibm_watsonx_ai.foundation_models as watson_models
            from ibm_watsonx_ai import Credentials
            from ibm_watsonx_ai.metanames import EmbedTextParamsMetaNames as EmbedParams
        except ImportError as e:
            raise ImportError(
                "IBM Watson dependencies are not installed. Please install them to use Watson embedding."
            ) from e

        class WatsonEmbeddingFunction: # TODO: Replace EmbeddingFunction with a suitable type, remove chromadb
            def __call__(self, input: Any) -> Any: # TODO: Replace Documents and Embeddings with suitable types
                if isinstance(input, str):
                    input = [input]

                embed_params = {
                    EmbedParams.TRUNCATE_INPUT_TOKENS: 3,
                    EmbedParams.RETURN_OPTIONS: {"input_text": True},
                }

                embedding = watson_models.Embeddings(
                    model_id=config.get("model"),
                    params=embed_params,
                    credentials=Credentials(
                        api_key=config.get("api_key"), url=config.get("api_url")
                    ),
                    project_id=config.get("project_id"),
                )

                try:
                    embeddings = embedding.embed_documents(input)
                    return cast(Any, embeddings) # TODO: Replace Embeddings with a suitable type
                except Exception as e:
                    print("Error during Watson embedding:", e)
                    raise e

        return WatsonEmbeddingFunction()

    @staticmethod
    def _configure_custom(config):
        custom_embedder = config.get("embedder")
        # if isinstance(custom_embedder, EmbeddingFunction): # TODO: Remove chromadb
        #     try:
        #         validate_embedding_function(custom_embedder) # TODO: Remove chromadb
        #         return custom_embedder
        #     except Exception as e:
        #         raise ValueError(f"Invalid custom embedding function: {str(e)}")
        # elif callable(custom_embedder):
        #     try:
        #         instance = custom_embedder()
        #         if isinstance(instance, EmbeddingFunction): # TODO: Remove chromadb
        #             validate_embedding_function(instance) # TODO: Remove chromadb
        #             return instance
        #         raise ValueError(
        #             "Custom embedder does not create an EmbeddingFunction instance" # TODO: Remove chromadb
        #         )
        #     except Exception as e:
        #         raise ValueError(f"Error instantiating custom embedder: {str(e)}")
        # else:
        #     raise ValueError(
        #         "Custom embedder must be an instance of `EmbeddingFunction` or a callable that creates one" # TODO: Remove chromadb
        #     )
        raise NotImplementedError("Custom ChromaDB embedding functions are no longer supported.")
