'use client'

import { useState, useEffect } from 'react'
import { History, Trash2, MessageSquare, Clock } from 'lucide-react'

interface ChatSession {
  id: string
  session_id: string
  title: string
  model_name: string
  messages: any[]
  created_at: string
  updated_at: string
}

interface ChatHistoryProps {
  onLoadChat: (sessionId: string, messages: any[]) => void
  currentSessionId?: string
}

export default function ChatHistory({ onLoadChat, currentSessionId }: ChatHistoryProps) {
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadChatHistory = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/api/chat-history')
      if (!response.ok) throw new Error('Failed to load chat history')

      const data = await response.json()
      setChatSessions(data)
      setError(null)
    } catch (err) {
      setError('Failed to load chat history')
      console.error('Error loading chat history:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadChatHistory()
  }, [])

  const deleteChat = async (sessionId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/chat-history/${sessionId}`, {
        method: 'DELETE'
      })

      if (!response.ok) throw new Error('Failed to delete chat')

      setChatSessions(prev => prev.filter(chat => chat.session_id !== sessionId))
    } catch (err) {
      console.error('Error deleting chat:', err)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  if (loading) {
    return (
      <div className="h-full bg-gray-900 p-4">
        <div className="flex items-center space-x-2 mb-4">
          <History className="w-5 h-5 text-gray-400" />
          <h3 className="font-semibold text-white">Chat History</h3>
        </div>
        <p className="text-sm text-gray-400">Loading...</p>
      </div>
    )
  }

  return (
    <div className="h-full bg-gray-900 flex flex-col">
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <History className="w-5 h-5 text-gray-400" />
            <h3 className="font-semibold text-white">Chat History</h3>
          </div>
          <button
            onClick={loadChatHistory}
            className="text-xs text-purple-400 hover:text-purple-300"
          >
            Refresh
          </button>
        </div>
        <p className="text-xs text-gray-500">{chatSessions.length} conversations</p>
      </div>

      <div className="flex-1 overflow-y-auto">
        {error && (
          <div className="p-4 text-sm text-red-400 bg-red-900/20 border-b border-red-800">
            {error}
          </div>
        )}

        {chatSessions.length === 0 ? (
          <div className="p-4 text-center">
            <MessageSquare className="w-12 h-12 text-gray-700 mx-auto mb-2" />
            <p className="text-sm text-gray-400">No chat history yet</p>
            <p className="text-xs text-gray-500 mt-1">Start a conversation to see it here</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-800">
            {chatSessions.map((chat) => (
              <div
                key={chat.id}
                className={`p-4 hover:bg-gray-800/50 cursor-pointer transition-colors ${
                  currentSessionId === chat.session_id ? 'bg-purple-900/20 border-l-4 border-purple-500' : ''
                }`}
                onClick={() => onLoadChat(chat.session_id, chat.messages)}
              >
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-medium text-sm text-white line-clamp-1 flex-1">
                    {chat.title || 'Untitled Chat'}
                  </h4>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      deleteChat(chat.session_id)
                    }}
                    className="text-gray-500 hover:text-red-400 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <div className="space-y-1">
                  <p className="text-xs text-gray-400 truncate">
                    Model: {chat.model_name}
                  </p>
                  <p className="text-xs text-gray-500 truncate">
                    {chat.messages.length} messages
                  </p>
                  <div className="flex items-center space-x-1 text-xs text-gray-500">
                    <Clock className="w-3 h-3" />
                    <span>{formatDate(chat.updated_at || chat.created_at)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
