"""Initial schema creation for VideoMind.

Revision ID: 001
Revises:
Create Date: 2026-10-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema."""
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_conversations_id', 'conversations', ['id'])

    # Create sources table
    op.create_table(
        'sources',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('uri', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('meta_data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sources_id', 'sources', ['id'])

    # Create chunks table
    op.create_table(
        'chunks',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('source_id', sa.String(36), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('meta_data', sa.JSON(), nullable=False),
        sa.Column('chroma_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chroma_id')
    )
    op.create_index('ix_chunks_id', 'chunks', ['id'])
    op.create_index('ix_chunks_source_id', 'chunks', ['source_id'])

    # Create conversation_sources table
    op.create_table(
        'conversation_sources',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('conversation_id', sa.String(36), nullable=False),
        sa.Column('source_id', sa.String(36), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_conversation_sources_id', 'conversation_sources', ['id'])
    op.create_index('ix_conversation_sources_conversation_id', 'conversation_sources', ['conversation_id'])
    op.create_index('ix_conversation_sources_source_id', 'conversation_sources', ['source_id'])

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('conversation_id', sa.String(36), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('citations', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_messages_id', 'messages', ['id'])
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index('ix_messages_conversation_id', table_name='messages')
    op.drop_index('ix_messages_id', table_name='messages')
    op.drop_table('messages')

    op.drop_index('ix_conversation_sources_source_id', table_name='conversation_sources')
    op.drop_index('ix_conversation_sources_conversation_id', table_name='conversation_sources')
    op.drop_index('ix_conversation_sources_id', table_name='conversation_sources')
    op.drop_table('conversation_sources')

    op.drop_index('ix_chunks_source_id', table_name='chunks')
    op.drop_index('ix_chunks_id', table_name='chunks')
    op.drop_table('chunks')

    op.drop_index('ix_sources_id', table_name='sources')
    op.drop_table('sources')

    op.drop_index('ix_conversations_id', table_name='conversations')
    op.drop_table('conversations')
