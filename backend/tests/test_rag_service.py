from types import SimpleNamespace

from app.core.config import Settings
from app.services.embeddings import DeterministicTestEmbeddingModel
from app.services.rag_service import RagService
from app.storage.local_storage import LocalFileStorage


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def join(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, top_k):
        self.rows = self.rows[:top_k]
        return self

    def all(self):
        return self.rows


class FakeDB:
    def __init__(self, rows):
        self.rows = rows

    def query(self, *args, **kwargs):
        return FakeQuery(self.rows)


def test_rag_retrieve_formats_results(tmp_path):
    settings = Settings(embedding_dimension=8)
    rag = RagService(
        settings=settings,
        storage=LocalFileStorage(tmp_path / "uploads"),
        embedding_model=DeterministicTestEmbeddingModel(dimension=8),
    )

    chunk = SimpleNamespace(id="c1", chunk_index=0, page_number=2, content="Important clause")
    file_obj = SimpleNamespace(filename="contract.pdf")
    db = FakeDB(rows=[(chunk, file_obj, 0.1)])

    results = rag.retrieve(db=db, query="clause", conversation_id=None, top_k=3)
    assert len(results) == 1
    assert results[0]["filename"] == "contract.pdf"
    assert results[0]["page_number"] == 2
    assert results[0]["score"] > 0.8
