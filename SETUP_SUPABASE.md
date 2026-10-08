# Supabase Setup Guide

## Prerequisites
1. Free Supabase account at https://supabase.com
2. Python 3.11+ with uv installed

## Steps

### 1. Create Supabase Project

1. Go to https://supabase.com and sign in
2. Click "New Project"
3. Fill in:
   - Project name: `videomind` (or any name)
   - Database password: Save this securely
   - Region: Choose closest to you (US, EU, APAC)
4. Click "Create new project" (takes 1-2 minutes)

### 2. Get Connection Details

Once project is created:
1. Go to Settings → API (left sidebar)
2. Copy:
   - `Project URL` → `SUPABASE_URL`
   - `anon` public key → `SUPABASE_KEY`
3. Create `.env` file in backend directory:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key
   GEMINI_API_KEY=your-gemini-key
   ```

### 3. Run Database Migrations

```bash
cd backend

# Install dependencies (if not already done)
uv pip install -r requirements.txt

# Run migrations to create tables
python -m alembic upgrade head
```

### 4. Verify Tables Created

In Supabase dashboard:
1. Go to SQL Editor
2. Click "New Query"
3. Run: `SELECT tablename FROM pg_tables WHERE schemaname='public';`
4. You should see: conversations, sources, chunks, messages, conversation_sources

## Troubleshooting

**Error: "Supabase credentials not configured"**
- Check `.env` file has SUPABASE_URL and SUPABASE_KEY
- Verify values are correct from Supabase dashboard

**Error: "could not translate host name"**
- Internet connection issue or Supabase project didn't finish creating
- Wait a few minutes, then try again

**Error: Running migrations**
- Make sure Python environment has alembic installed
- Run: `uv pip install alembic sqlalchemy`
