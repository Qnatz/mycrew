import unittest
from unittest.mock import patch, MagicMock, call
import numpy as np
import shutil
import os

# Assuming KnowledgeBaseTool is in mycrews.qrew.tools.knowledge_base_tool
from mycrews.qrew.tools.knowledge_base_tool import KnowledgeBaseTool
import mycrews.qrew.tools.knowledge_base_tool as kbt_module # For patching constants if needed

class TestKnowledgeBaseTool(unittest.TestCase):

    def setUp(self):
        # Mock ONNX session and Tokenizer to avoid loading real models
        self.mock_onnx_session = MagicMock()
        # Mock the return value of run method for onnx session
        # It should be a list containing a numpy array representing token embeddings
        # Shape: (batch_size, sequence_length, embedding_dim)
        # _embed_text takes [0][0] of this, resulting in (sequence_length, embedding_dim)
        # then averages over sequence_length.
        self.mock_onnx_session.run.return_value = [np.random.rand(1, 10, 768).astype(np.float32)]


        self.mock_tokenizer = MagicMock()
        # Mock tokenizer encode method
        self.mock_tokenizer.encode.return_value = MagicMock(ids=[1,2,3], attention_mask=[1,1,1], type_ids=[0,0,0])


        self.patcher_ort_session = patch('onnxruntime.InferenceSession', return_value=self.mock_onnx_session)
        self.patcher_tokenizer_file = patch('tokenizers.Tokenizer.from_file', return_value=self.mock_tokenizer)

        self.mock_ort_session_start = self.patcher_ort_session.start()
        self.mock_tokenizer_file_start = self.patcher_tokenizer_file.start()

        # Define a temporary path for ChromaDB storage used by KBT instance during tests.
        # KnowledgeBaseTool's __init__ uses a default kb_persist_path="kb_chroma_storage".
        # We will let it use that and clean it up.
        self.test_kb_storage_path = "kb_chroma_storage"
        if os.path.exists(self.test_kb_storage_path):
            shutil.rmtree(self.test_kb_storage_path)
        # No need to os.makedirs here, ChromaDB PersistentClient handles it.

        self.kb_tool = KnowledgeBaseTool(
            onnx_model_path="dummy/model.onnx",
            tokenizer_path="dummy/tokenizer.json"
            # kb_persist_path could be passed here if KBT is modified to accept it.
            # For now, it uses its default "kb_chroma_storage".
        )

    def tearDown(self):
        self.patcher_ort_session.stop()
        self.patcher_tokenizer_file.stop()

        if hasattr(self.kb_tool, 'kb_client') and self.kb_tool.kb_client:
            try:
                # Attempt to gracefully shutdown or clear client if necessary
                # For PersistentClient, deleting the directory is the main cleanup for tests.
                # If specific collections were added outside the default "knowledge_base", clear them.
                # self.kb_tool.kb_client.clear() # Or similar if available and needed
                pass
            except Exception as e:
                print(f"Test teardown: Error during kb_client handling: {e}")

        # Clean up the ChromaDB storage directory used by KnowledgeBaseTool
        if os.path.exists(self.test_kb_storage_path):
            #print(f"Tearing down, removing {self.test_kb_storage_path}")
            shutil.rmtree(self.test_kb_storage_path)


    def test_initialization(self):
        """Test that KnowledgeBaseTool initializes its kb_client and kb_collection."""
        self.assertIsNotNone(self.kb_tool.kb_client, "KB Client should be initialized.")
        self.assertIsNotNone(self.kb_tool.kb_collection, "KB Collection should be initialized.")
        self.assertEqual(self.kb_tool.kb_collection.name, "knowledge_base")
        # Check that the mocked ONNX and Tokenizer were called during init
        self.mock_ort_session_start.assert_called_with("dummy/model.onnx", unittest.mock.ANY)
        self.mock_tokenizer_file_start.assert_called_with("dummy/tokenizer.json")

    @patch.object(KnowledgeBaseTool, '_embed_text')
    def test_call_embedding_interface(self, mock_embed_text):
        """Test the __call__ method (embedding function interface)."""
        # Define a consistent embedding dimension for the test
        embedding_dim = 768
        dummy_embedding_list = [0.1] * embedding_dim
        mock_embed_text.return_value = np.array(dummy_embedding_list, dtype=np.float32)

        texts = ["hello world", "test sentence"]
        embeddings = self.kb_tool(texts) # Invokes __call__

        self.assertEqual(len(embeddings), 2, "Should return embeddings for each text.")
        self.assertIsInstance(embeddings[0], list, "Each embedding should be a list.")
        # Only check length if embedding was successful.
        # The __call__ method in KBT has a dynamic dim check now.
        # If mock_embed_text was called, the dimension should match.
        if embeddings and embeddings[0]:
             self.assertEqual(len(embeddings[0]), embedding_dim, f"Embedding dimension should be {embedding_dim}.")
             self.assertAlmostEqual(embeddings[0][0], 0.1, places=5)

        mock_embed_text.assert_has_calls([call("hello world"), call("test sentence")])

    @patch.object(KnowledgeBaseTool, '_embed_text')
    def test_run_query_found(self, mock_embed_text):
        """Test the _run method when a query finds results."""
        embedding_dim = 768 # Should match the KBT's understanding or be dynamically set
        mock_embed_text.return_value = np.array([0.5] * embedding_dim, dtype=np.float32)

        mock_query_result = {
            "ids": [["id1", "id2"]], # Two results for the query
            "documents": [["doc1_content", "doc2_content"]],
            "metadatas": [[{"source": "doc1_source"}, {"source": "doc2_source"}]],
            "distances": [[0.2, 0.3]]
        }

        # Replace the actual kb_collection with a mock
        self.kb_tool.kb_collection = MagicMock()
        self.kb_tool.kb_collection.query.return_value = mock_query_result

        result_str = self.kb_tool._run("test query string")

        self.kb_tool.kb_collection.query.assert_called_once()
        # We can be more specific about query arguments if needed:
        # called_args, called_kwargs = self.kb_tool.kb_collection.query.call_args
        # self.assertEqual(called_kwargs['query_embeddings'], [[0.5] * embedding_dim])
        # self.assertEqual(called_kwargs['n_results'], 3) # Default max_context is 3

        self.assertIn("doc1_content", result_str, "Document 1 content should be in result string.")
        self.assertIn("doc1_source", result_str, "Document 1 metadata (source) should be in result string.")
        self.assertIn("doc2_content", result_str, "Document 2 content should be in result string.")
        self.assertIn("doc2_source", result_str, "Document 2 metadata (source) should be in result string.")

    @patch.object(KnowledgeBaseTool, '_embed_text')
    def test_run_query_not_found(self, mock_embed_text):
        """Test the _run method when a query finds no results."""
        embedding_dim = 768
        mock_embed_text.return_value = np.array([0.5] * embedding_dim, dtype=np.float32)

        # Mock query to return empty results
        self.kb_tool.kb_collection = MagicMock()
        self.kb_tool.kb_collection.query.return_value = {"documents": [[]], "metadatas": [[]], "ids": [[]], "distances": [[]]}

        result_str = self.kb_tool._run("another test query")
        self.assertIn("No relevant information found", result_str)

    def test_embed_text_with_mocked_dependencies(self):
        """Test the _embed_text method using the mocked ONNX and tokenizer from setUp."""
        text_to_embed = "This is a test sentence for _embed_text."
        embedding = self.kb_tool._embed_text(text_to_embed)

        self.assertIsNotNone(embedding, "_embed_text should return an embedding, not None.")
        self.assertIsInstance(embedding, np.ndarray, "Embedding should be a numpy array.")
        # The shape depends on the mocked ONNX model's output dimension (768 in this case)
        self.assertEqual(embedding.shape, (768,), f"Embedding shape mismatch. Expected (768,), got {embedding.shape}")

        # Verify that the mocked tokenizer and session were used as expected
        self.mock_tokenizer.encode.assert_called_with(text_to_embed)
        self.mock_onnx_session.run.assert_called_with(None, {
            "input_ids": np.array([[1,2,3]], dtype=np.int64),
            "attention_mask": np.array([[1,1,1]], dtype=np.int64),
            "token_type_ids": np.array([[0,0,0]], dtype=np.int64)
        })

    @patch.object(KnowledgeBaseTool, '_embed_text')
    def test_run_with_dict_input(self, mock_embed_text):
        """Test _run method with dictionary input."""
        embedding_dim = 768
        mock_embed_text.return_value = np.array([0.5] * embedding_dim, dtype=np.float32)

        mock_query_result = {
            "ids": [["id1"]], "documents": [["doc1_content"]],
            "metadatas": [[{"source": "doc1_source"}]],"distances": [[0.2]]
        }
        self.kb_tool.kb_collection = MagicMock()
        self.kb_tool.kb_collection.query.return_value = mock_query_result

        input_dict = {"question": "test query from dict", "max_context": 2}
        result_str = self.kb_tool._run(input_dict)

        self.kb_tool.kb_collection.query.assert_called_once()
        # Check if n_results was passed correctly
        _, called_kwargs = self.kb_tool.kb_collection.query.call_args
        self.assertEqual(called_kwargs.get('n_results'), 2)
        self.assertIn("doc1_content", result_str)


if __name__ == '__main__':
    unittest.main()
