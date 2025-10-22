# LLM-Powered Conversational Agent

A Streamlit-based conversational agent using OpenAI's gpt-4o-mini with conversation storage and automated summarization in Supabase.

## Features

- Real-time chat with gpt-4o-mini
- Session persistence with unique IDs
- Manual conversation end trigger
- Automatic summary + structured evaluation on end
- Supabase storage for all conversations
- Public deployment via Streamlit Cloud
- Shareable conversation links

## Setup

### 1. Supabase Setup

1. Create a free account at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to the SQL Editor and run this schema:

```sql
-- Create conversations table
CREATE TABLE conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    messages JSONB NOT NULL,
    summary TEXT,
    evaluation JSONB,
    ended_at TIMESTAMP WITH TIME ZONE
);

-- Create index for better query performance
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);
```

4. Go to Settings > API to get your:
   - Project URL
   - Anon public key

### 2. Environment Variables

1. Copy the example secrets file:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

2. Edit `.streamlit/secrets.toml` with your actual API keys:
```toml
[general]
TEST_MODE = false
OPENAI_API_KEY = "your_openai_api_key_here"

[database]
SUPABASE_URL = "your_supabase_url_here"
SUPABASE_KEY = "your_supabase_anon_key_here"
```

### Test Mode

For testing the app without going through the full interview flow, set `TEST_MODE=true` in your `secrets.toml` file. This will:

- Use a simplified system prompt that asks only 2 questions
- Guide users to end the conversation quickly
- Perfect for e2e testing of the app flow

When `TEST_MODE=true`, the AI will:
1. Ask for your name and brief background
2. Ask one follow-up question
3. Immediately guide you to click "End Conversation"

### 3. Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
streamlit run app.py
```

3. Open your browser to `http://localhost:8501`

## Deployment on Streamlit Cloud

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. In the app settings, go to "Advanced settings" and add your secrets in TOML format:

```toml
[general]
TEST_MODE = false
OPENAI_API_KEY = "your_openai_api_key_here"

[database]
SUPABASE_URL = "your_supabase_url_here"
SUPABASE_KEY = "your_supabase_anon_key_here"
```

## Querying Stored Conversations

You can query your conversations directly in Supabase:

```sql
-- Get all conversations
SELECT * FROM conversations ORDER BY created_at DESC;

-- Get conversations with summaries
SELECT session_id, created_at, summary, evaluation 
FROM conversations 
WHERE summary IS NOT NULL;

-- Get conversation by session ID
SELECT * FROM conversations WHERE session_id = 'your-session-id';
```

## Project Structure

```
newco-ai-agent/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .streamlit/
│   ├── secrets.toml.example # Template for secrets (in git)
│   └── secrets.toml        # Local secrets (not in git)
├── .gitignore            # Git ignore file
├── README.md             # Setup and deployment instructions
└── utils/
    ├── __init__.py
    ├── openai_client.py  # OpenAI API wrapper
    ├── supabase_client.py # Supabase database operations
    └── prompts.py        # System prompt configuration
```
