"""Initial Migration

Revision ID: 25402575183c
Revises: 
Create Date: 2024-01-24 01:57:07.728851

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '25402575183c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('sub', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('picture', sa.String(), nullable=True),
    sa.Column('space', sa.Integer(), nullable=True),
    sa.Column('max_space', sa.BigInteger(), nullable=True),
    sa.Column('password', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('edited_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('files',
    sa.Column('file_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('file_name', sa.String(), nullable=True),
    sa.Column('total_chunks', sa.Integer(), nullable=True),
    sa.Column('is_complete', sa.Boolean(), nullable=True),
    sa.Column('size', sa.BigInteger(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('edited_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('file_id')
    )
    op.create_index(op.f('ix_files_file_id'), 'files', ['file_id'], unique=False)
    op.create_index(op.f('ix_files_file_name'), 'files', ['file_name'], unique=False)
    op.create_table('chunks',
    sa.Column('chunk_id', sa.Integer(), nullable=False),
    sa.Column('file_id', sa.Integer(), nullable=True),
    sa.Column('sequence_number', sa.Integer(), nullable=True),
    sa.Column('data', sa.LargeBinary(), nullable=True),
    sa.Column('is_received', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('edited_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['file_id'], ['files.file_id'], ),
    sa.PrimaryKeyConstraint('chunk_id')
    )
    op.create_index(op.f('ix_chunks_chunk_id'), 'chunks', ['chunk_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_chunks_chunk_id'), table_name='chunks')
    op.drop_table('chunks')
    op.drop_index(op.f('ix_files_file_name'), table_name='files')
    op.drop_index(op.f('ix_files_file_id'), table_name='files')
    op.drop_table('files')
    op.drop_table('users')
    # ### end Alembic commands ###
