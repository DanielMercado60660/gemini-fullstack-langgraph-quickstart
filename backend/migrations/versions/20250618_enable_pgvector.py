"""enable pgvector extension and create documents tables"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20250618_enable_pgvector"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create documents and document_chunks tables."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute(
        """
        CREATE TABLE documents (
            id BIGSERIAL PRIMARY KEY,
            source TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE document_chunks (
            id BIGSERIAL PRIMARY KEY,
            document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding VECTOR(768) NOT NULL
        )
        """
    )

    op.execute(
        "CREATE INDEX document_chunks_embedding_idx ON document_chunks USING ivfflat (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    """Drop created tables and extension."""
    op.execute("DROP INDEX IF EXISTS document_chunks_embedding_idx")
    op.execute("DROP TABLE IF EXISTS document_chunks")
    op.execute("DROP TABLE IF EXISTS documents")
    op.execute("DROP EXTENSION IF EXISTS vector")

