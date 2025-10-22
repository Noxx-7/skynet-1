'use client'

import { useState } from 'react'
import { Users, Share2, MessageSquare, Eye } from 'lucide-react'

interface Participant {
  id: string
  name: string
  email: string
  role: 'owner' | 'editor' | 'viewer'
}

export default function CollaborationPanel() {
  const [participants, setParticipants] = useState<Participant[]>([
    { id: '1', name: 'You', email: 'you@example.com', role: 'owner' },
    { id: '2', name: 'John Doe', email: 'john@example.com', role: 'editor' },
    { id: '3', name: 'Jane Smith', email: 'jane@example.com', role: 'viewer' },
  ])

  const [sessionLink, setSessionLink] = useState('https://llm-playground.com/session/abc123')
  const [chatMessages, setChatMessages] = useState([
    { id: '1', user: 'John Doe', message: 'Hey, I made some changes to the model wrapper', time: '2:30 PM' },
    { id: '2', user: 'You', message: 'Thanks! I\'ll review them', time: '2:31 PM' },
  ])
  const [newMessage, setNewMessage] = useState('')

  const copySessionLink = () => {
    navigator.clipboard.writeText(sessionLink)
    alert('Session link copied to clipboard!')
  }

  const sendMessage = () => {
    if (!newMessage.trim()) return

    const message = {
      id: Date.now().toString(),
      user: 'You',
      message: newMessage,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    setChatMessages(prev => [...prev, message])
    setNewMessage('')
  }

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'owner':
        return <Users className="w-4 h-4 text-green-600" />
      case 'editor':
        return <Share2 className="w-4 h-4 text-blue-600" />
      case 'viewer':
        return <Eye className="w-4 h-4 text-gray-600" />
      default:
        return null
    }
  }

  return (
    <div className="space-y-6">
      {/* Session Info */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="font-semibold mb-4 flex items-center">
          <Users className="w-5 h-5 mr-2" />
          Collaboration Session
        </h3>
        
        <div className="space-y-3">
          <div>
            <label className="text-sm font-medium text-gray-700">Session Link</label>
            <div className="flex space-x-2 mt-1">
              <input
                type="text"
                value={sessionLink}
                readOnly
                className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm bg-gray-50"
              />
              <button
                onClick={copySessionLink}
                className="px-3 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
              >
                Copy
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Participants */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h4 className="font-medium mb-3">Participants ({participants.length})</h4>
        <div className="space-y-2">
          {participants.map((participant) => (
            <div key={participant.id} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-blue-600">
                    {participant.name.split(' ').map(n => n[0]).join('')}
                  </span>
                </div>
                <div>
                  <div className="text-sm font-medium">{participant.name}</div>
                  <div className="text-xs text-gray-500">{participant.email}</div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {getRoleIcon(participant.role)}
                <span className="text-xs text-gray-500 capitalize">{participant.role}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Chat */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h4 className="font-medium mb-3 flex items-center">
          <MessageSquare className="w-4 h-4 mr-2" />
          Session Chat
        </h4>
        
        <div className="space-y-3 mb-4 max-h-40 overflow-y-auto">
          {chatMessages.map((msg) => (
            <div key={msg.id} className="text-sm">
              <div className="flex justify-between">
                <span className="font-medium">{msg.user}</span>
                <span className="text-gray-500 text-xs">{msg.time}</span>
              </div>
              <p className="text-gray-700 mt-1">{msg.message}</p>
            </div>
          ))}
        </div>

        <div className="flex space-x-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type a message..."
            className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <button
            onClick={sendMessage}
            disabled={!newMessage.trim()}
            className="px-3 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}