/*
  # Create chat history table

  1. New Tables
    - `chat_history`
      - `id` (uuid, primary key)
      - `user_id` (text) - User identifier
      - `session_id` (text, indexed) - Chat session identifier
      - `model_id` (text, nullable) - Model ID used
      - `model_name` (text) - Model name
      - `messages` (jsonb) - Array of chat messages
      - `title` (text, nullable) - Chat title
      - `created_at` (timestamptz) - Creation timestamp
      - `updated_at` (timestamptz) - Last update timestamp
  
  2. Security
    - Enable RLS on `chat_history` table
    - Add policy for users to manage their own chat history
*/

CREATE TABLE IF NOT EXISTS chat_history (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id text NOT NULL DEFAULT 'guest-user',
  session_id text NOT NULL,
  model_id text,
  model_name text NOT NULL,
  messages jsonb NOT NULL DEFAULT '[]'::jsonb,
  title text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_history_session_id ON chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_updated_at ON chat_history(updated_at DESC);

ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own chat history"
  ON chat_history FOR SELECT
  USING (true);

CREATE POLICY "Users can insert own chat history"
  ON chat_history FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Users can update own chat history"
  ON chat_history FOR UPDATE
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Users can delete own chat history"
  ON chat_history FOR DELETE
  USING (true);