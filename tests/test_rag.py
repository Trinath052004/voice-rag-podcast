```language tests/test_rag.py
import pytest
from app.rag.retriever import retrieve


def test_retrieve():
    result = retrieve("test query")
    assert isinstance(result, list)


def test_retrieve_empty():
    result = retrieve("nonexistent query")
    assert isinstance(result, list)
    # add a check to see if the list returned is empty
    # if the qdrant DB is empty, the result should be empty
    # please populate the DB before running this test
    # for a more robust test
    # assert len(result) == 0

```