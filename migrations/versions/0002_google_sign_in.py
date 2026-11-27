"""google sign in

Revision ID: 0002_google_sign_in
Revises: 0001_baseline
Create Date: 2026-11-27 16:41:56.749944

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_google_sign_in"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("google_sub", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column(
            "auth_provider",
            sa.String(length=20),
            server_default="local",
            nullable=True,
        ),
    )
    op.add_column(
        "users", sa.Column("avatar_url", sa.String(length=500), nullable=True)
    )
    op.alter_column(
        "users",
        "email",
        existing_type=sa.VARCHAR(length=50),
        type_=sa.String(length=255),
        existing_nullable=False,
    )
    op.alter_column(
        "users", "password", existing_type=sa.VARCHAR(length=128), nullable=True
    )
    op.create_unique_constraint("users_google_sub_key", "users", ["google_sub"])


def downgrade() -> None:
    # Going back would lose Google-only accounts or truncate emails: refuse
    # instead of failing halfway or silently dropping data.
    conn = op.get_bind()
    blocking = conn.execute(
        sa.text(
            "SELECT count(*) FROM users " "WHERE password IS NULL OR length(email) > 50"
        )
    ).scalar()
    if blocking:
        raise RuntimeError(
            f"{blocking} user(s) have no password or an email longer than 50 "
            "characters: fix or delete them before downgrading."
        )

    op.drop_constraint("users_google_sub_key", "users", type_="unique")
    op.alter_column(
        "users", "password", existing_type=sa.VARCHAR(length=128), nullable=False
    )
    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(length=255),
        type_=sa.VARCHAR(length=50),
        existing_nullable=False,
    )
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "auth_provider")
    op.drop_column("users", "google_sub")
