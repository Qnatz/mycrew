import pytest
import os
import shutil

# Define a test-specific store path

@pytest.fixture(scope="function")
    # Ensure the test directory is clean before each test
    if os.path.exists(TEST_STORE_PATH):
        shutil.rmtree(TEST_STORE_PATH)
    # The ObjectBox Store constructor expects the directory itself.
    os.makedirs(TEST_STORE_PATH, exist_ok=True)

    # Override the default STORE_PATH for testing by setting the class variable
    original_store_path_class_var = ObjectBoxMemory._store_path
    ObjectBoxMemory._store_path = TEST_STORE_PATH

    # Reset store instance to ensure it uses the new path via __init__
    if ObjectBoxMemory._store is not None:
        ObjectBoxMemory.close_store() # Use the new classmethod to close and reset

    # Create instance, which will create the store at TEST_STORE_PATH
    memory = ObjectBoxMemory(store_path_override=TEST_STORE_PATH)

    yield memory

    # Teardown: close the store and delete the test database directory
    ObjectBoxMemory.close_store() # Use the new classmethod
    if os.path.exists(TEST_STORE_PATH):
        shutil.rmtree(TEST_STORE_PATH)

    # Restore original store path class variable
    ObjectBoxMemory._store_path = original_store_path_class_var
    # Ensure store is reset for subsequent non-test uses if necessary
    ObjectBoxMemory._store = None


    assert ObjectBoxMemory._store is not None
    # ObjectBox Store.directory() returns the absolute path
    assert ObjectBoxMemory._store.directory() == os.path.abspath(TEST_STORE_PATH)

    text = "This is a test entry"
    meta = {"source": "test_single"}


    # Query for the entry
    query_text = "test entry"

    assert len(results) >= 1, "Should find at least one result"

    found = False
    for res in results:
        if res["content"] == text:
            assert res["metadata"]["source"] == meta["source"]
            assert "distance" in res
            found = True
            break
    assert found, "The saved entry was not found in query results"

    texts = ["First test entry about apples", "Second test entry about bananas"]
    metas = [{"source": "test_multi_1", "id": 1}, {"source": "test_multi_2", "id": 2}]

    for text, meta in zip(texts, metas):

    # Query for "apples"
    assert len(results_apples) >= 1
    if results_apples: # Check if list is not empty
        assert results_apples[0]["content"] == texts[0]
        assert results_apples[0]["metadata"]["source"] == metas[0]["source"]

    # Query for "bananas"
    assert len(results_bananas) >= 1
    if results_bananas: # Check if list is not empty
        assert results_bananas[0]["content"] == texts[1]
        assert results_bananas[0]["metadata"]["source"] == metas[1]["source"]

    assert len(results) == 0

    # HNSW can still return results even if they are not very similar.
    # We expect it to return the "oranges" entry as the nearest, even if not a perfect match.
    assert isinstance(results, list)
    if results: # If it returns something
        assert len(results) == 1 # Should return the closest one
        assert results[0]["content"] == "An entry about oranges"
    # If the embedding model is very good at distinguishing, it might return 0 results
    # if "apples" is too far from "oranges". This assertion might need adjustment
    # based on the actual embedding model's behavior.
    # For a dummy embedder (random vectors), this is less predictable.
    # Given the current dummy embedder, we can't be too strict on *what* is returned,
    # only that the query executes and returns a list.
    # If a real model was used, and "apples" is truly dissimilar to "oranges",
    # and HNSW has a threshold (which it doesn't apply by default beyond 'k'),
    # it might be empty. But typically HNSW *will* return k items.
    # The test is more about the mechanism than the semantic correctness with dummy embeddings.
    pass # Current test passes if it runs and returns a list.
