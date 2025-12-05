"""Add trigram indexes for description genre and isbn

Revision ID: 692eb6e03559
Revises: aa376f4a6cc4
Create Date: 2025-12-01 18:25:33.404548

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "692eb6e03559"
down_revision: Union[str, Sequence[str], None] = "aa376f4a6cc4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add trigram indexes for description, genre, and isbn columns."""
    # Create trigram indexes for fuzzy search
    op.create_index(
        "​ix_books_description_trgm",
        "books",
        ["description"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"description": "gin_trgm_ops"},
    )

    op.create_index(
        "ix_books_genre_trgm",
        "books",
        ["genre"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"genre": "gin_trgm_ops"},
    )

    op.create_index(
        "ix_books_isbn_trgm",
        "books",
        ["isbn"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"isbn": "gin_trgm_ops"},
    )


def downgrade() -> None:
    """Remove trigram indexes for description, genre, and isbn."""
    op.drop_index(
        "ix_books_isbn_trgm",
        table_name="books",
        postgresql_using="gin",
        postgresql_ops={"isbn": "gin_trgm_ops"},
    )
    op.drop_index(
        "ix_books_genre_trgm",
        table_name="books",
        postgresql_using="gin",
        postgresql_ops={"genre": "gin_trgm_ops"},
    )
    op.drop_index(
        "ix_books_description_trgm",
        table_name="books",
        postgresql_using="gin",
        postgresql_ops={"description": "gin_trgm_ops"},
    )
