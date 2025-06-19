import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import os
import shutil

# Assuming tools are accessible in the python path
# If not, sys.path manipulations might be needed for a real test environment
from tools.embedder import embed as tools_embedder_embed
from mycrews.qrew.tools.use_lite_embedding_tool import USELiteEmbeddingTool
from src.crewai.knowledge.storage.knowledge_storage import KnowledgeStorage

# Helper function to create a dummy USELiteEmbeddingTool for mocking
def mock_use_lite_embed(text: str):
    # Simple hash-based embedding for deterministic testing
    # In a real scenario, you might want more controlled vectors
    if text == "query text":
        return np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)
    elif text == "doc1":
        return np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32) # Exact match
    elif text == "doc2":
        return np.array([0.5, 0.4, 0.3, 0.2, 0.1], dtype=np.float32) # Different
    elif text == "doc3":
        return np.array([0.11, 0.21, 0.31, 0.41, 0.51], dtype=np.float32) # Close match
    else:
        # Fallback for any other text to ensure the mock always returns a compatible array
        # Hash the text to get a somewhat deterministic vector for other inputs
        hash_val = hash(text)
        arr = np.array([
            (hash_val % 1000) / 1000.0,
            ((hash_val >> 10) % 1000) / 1000.0,
            ((hash_val >> 20) % 1000) / 1000.0,
            ((hash_val >> 30) % 1000) / 1000.0,
            ((hash_val >> 40) % 1000) / 1000.0,
        ], dtype=np.float32)
        return arr / np.linalg.norm(arr) if np.linalg.norm(arr) > 0 else arr


class TestKnowledgeIntegration(unittest.TestCase):

    def setUp(self):
        # Ensure a clean state for test paths
        self.test_db_path_ks = ".test_db/ks_test_collection" # Path used by KnowledgeStorage via db_storage_path()

        # Clean up before each test if paths exist
            # Need to ensure ObjectBox store is closed if a previous test failed mid-operation
            try:
                ObjectBoxMemory.close_store()
            except Exception:
                pass # Ignore if not initialized or already closed

        # For KnowledgeStorage, the path is constructed internally, so we need to anticipate it
        # We will let KnowledgeStorage create and manage its own path based on its logic,
        # but ensure the root .db dir is clean if needed or specific test collection dirs.
        # For now, ObjectBoxMemory tests handle their specific path. KS tests will use mocks primarily for ObjectBox.


    def tearDown(self):
        # Clean up after each test
            try:
                ObjectBoxMemory.close_store()
            except Exception:
                pass

        # If KnowledgeStorage tests create actual DBs (not fully mocked), clean them up too.
        # Example path based on KnowledgeStorage logic:
        if os.path.exists(ks_test_path):
            try:
                # Assuming KnowledgeStorage uses the same shared ObjectBoxMemory store logic for closing
                ObjectBoxMemory.close_store()
            except Exception:
                pass
            shutil.rmtree(ks_test_path)

        # General cleanup of .db folder if it's a root for tests.
        # This might be too broad if other tests use .db, so be cautious.
        # For now, specific cleanup is preferred.
        # test_root_db_dir = ".db"
        # if os.path.exists(test_root_db_dir) and not os.listdir(test_root_db_dir): # if empty
        #     shutil.rmtree(test_root_db_dir)


    def test_tools_embedder_uses_use_lite(self):
        """Test that tools.embedder.embed calls USELiteEmbeddingTool.embed"""
        with patch('mycrews.qrew.tools.use_lite_embedding_tool.USELiteEmbeddingTool.embed', return_value=np.array([1.0, 0.5])) as mock_tool_embed:
            # Patch the constructor of USELiteEmbeddingTool to avoid model loading issues in test
            # and to be able to assert calls on the instance if needed.
            mock_use_lite_instance = MagicMock()
            mock_use_lite_instance.embed.return_value = np.array([1.0, 0.5]) # normalized-like

            with patch('mycrews.qrew.tools.use_lite_embedding_tool.USELiteEmbeddingTool.__init__', return_value=None):
                # Re-patch embed on the class used by tools.embedder
                with patch('tools.embedder.USELiteEmbeddingTool.embed', new=mock_tool_embed):
                    texts = ["hello world"]
                    # tools_embedder_embed instantiates USELiteEmbeddingTool internally
                    embeddings = tools_embedder_embed(texts)
                    mock_tool_embed.assert_called_once_with("hello world")
                    self.assertEqual(len(embeddings), 1)
                    # Check if the returned vector is a normalized version of what the mock returned
                    # Original mock output: np.array([1.0, 0.5])
                    # Norm = sqrt(1*1 + 0.5*0.5) = sqrt(1.25) approx 1.118
                    # Expected: [1.0/1.118, 0.5/1.118] = [0.894, 0.447]
                    expected_norm_vec = np.array([1.0, 0.5]) / np.linalg.norm(np.array([1.0, 0.5]))
                    np.testing.assert_array_almost_equal(embeddings[0], expected_norm_vec, decimal=3)


    @patch('tools.embedder.embed') # Mock the actual embedding function used by ObjectBoxMemory
        """Test ObjectBoxMemory save and query methods with mocked embeddings."""
        mock_tools_embed.side_effect = lambda texts: [mock_use_lite_embed(t) for t in texts]


        memory.save("doc1", {"source": "A"}) # Embeds as [0.1, 0.2, 0.3, 0.4, 0.5]
        memory.save("doc2", {"source": "B"}) # Embeds as [0.5, 0.4, 0.3, 0.2, 0.1]
        memory.save("doc3", {"source": "C"}) # Embeds as [0.11, 0.21, 0.31, 0.41, 0.51]

        # Query vector for "query text" is [0.1, 0.2, 0.3, 0.4, 0.5]
        results = memory.query("query text", limit=2, score_threshold=0.9)

        self.assertEqual(len(results), 2)
        # Result 0: doc1 (exact match with query text embedding)
        self.assertAlmostEqual(results[0]['score'], 1.0, places=5)
        self.assertEqual(results[0]['content'], "doc1")
        self.assertEqual(results[0]['metadata']['source'], "A")

        # Result 1: doc3 (close match with query text embedding)
        # Similarity(query_text, doc3)
        # qvec = [0.1, 0.2, 0.3, 0.4, 0.5] (norm approx 0.7416)
        # d3vec = [0.11, 0.21, 0.31, 0.41, 0.51] (norm approx 0.777)
        # dot_product = 0.011 + 0.042 + 0.093 + 0.164 + 0.255 = 0.565
        # similarity = 0.565 / (np.linalg.norm(qvec) * np.linalg.norm(d3vec))
        # Assuming vectors are normalized by embedder (as they should be by mock_use_lite_embed if norm > 0)
        # and also by tools.embedder.embed.
        # The mock_use_lite_embed for "query text" and "doc1" are identical.
        # The mock_use_lite_embed for "doc3" is slightly different.
        # The query method in ObjectBoxMemory re-normalizes for safety, so scores are true cosine sims.

        q_vec_norm = mock_use_lite_embed("query text")
        doc3_vec_norm = mock_use_lite_embed("doc3")
        expected_sim_doc3 = np.dot(q_vec_norm, doc3_vec_norm) / (np.linalg.norm(q_vec_norm) * np.linalg.norm(doc3_vec_norm))

        self.assertAlmostEqual(results[1]['score'], expected_sim_doc3, places=5)
        self.assertTrue(results[1]['score'] >= 0.9) # check threshold
        self.assertEqual(results[1]['content'], "doc3")
        self.assertEqual(results[1]['metadata']['source'], "C")

        # Clean up is handled by tearDown

    @patch('src.crewai.knowledge.storage.knowledge_storage.ObjectBoxMemory')
        """Test that KnowledgeStorage correctly delegates to ObjectBoxMemory."""
        mock_ob_memory_instance = MagicMock(spec=ObjectBoxMemory)
        mock_ob_memory_instance.query.return_value = [
            {"content": "test content", "metadata": {"source": "test"}, "score": 0.95, "id": "obj_id_1"}
        ]
        # This path is used by the mocked instance for assertion, not for actual file creation here.
        mock_ob_memory_instance._current_store_actual_path = "/mocked/path/to/store/test_collection"
        mock_ob_memory_class.return_value = mock_ob_memory_instance

        ks = KnowledgeStorage(collection_name="test_collection")

        ks.save(["doc1"], [{"meta": "data"}])
        mock_ob_memory_instance.save.assert_called_once_with(value="doc1", metadata={"meta": "data"})

        mock_ob_memory_instance.save.reset_mock()

        results = ks.search(["query text"], limit=1, score_threshold=0.9)
        mock_ob_memory_instance.query.assert_called_once_with(query_text="query text", limit=1, score_threshold=0.9)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['context'], "test content")
        self.assertEqual(results[0]['id'], "obj_id_1")

        mock_ob_memory_instance.reset_mock()
        # Reset call count for the class mock as well, as __init__ is called during reset
        mock_ob_memory_class.reset_mock()
        mock_ob_memory_class.return_value = mock_ob_memory_instance # re-assign after reset

        with patch('src.crewai.knowledge.storage.knowledge_storage.shutil.rmtree') as mock_rmtree:
            with patch('src.crewai.knowledge.storage.knowledge_storage.ObjectBoxMemory.close_store') as mock_close_store:
                ks.reset()
                mock_close_store.assert_called_once()
                # KnowledgeStorage.reset should re-initialize ObjectBoxMemory by calling its constructor
                mock_ob_memory_class.assert_called_once()
                # Assert rmtree was called with the path stored in the (mocked) db_memory instance
                mock_rmtree.assert_called_once_with(mock_ob_memory_instance._current_store_actual_path)


if __name__ == '__main__':
    unittest.main()
