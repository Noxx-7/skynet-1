'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Users, Plus, Home, Brain, Video, MessageSquare,
  Share2, Clock, CheckCircle
} from 'lucide-react';

interface CollaborationSession {
  id: string;
  name: string;
  session_id: string;
  description?: string;
  created_by: string;
  participants: string[];
  shared_models: string[];
  is_active: boolean;
  created_at: string;
}

export default function CollaboratePage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<CollaborationSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newSessionName, setNewSessionName] = useState('');
  const [newSessionDesc, setNewSessionDesc] = useState('');

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const response = await fetch('/api/collaboration/sessions');
      if (response.ok) {
        const data = await response.json();
        setSessions(data);
      }
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const createSession = async () => {
    if (!newSessionName.trim()) return;

    try {
      const response = await fetch('/api/collaboration/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: newSessionName,
          description: newSessionDesc
        })
      });

      if (response.ok) {
        await fetchSessions();
        setShowCreateModal(false);
        setNewSessionName('');
        setNewSessionDesc('');
      }
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900">
      {/* Header */}
      <header className="border-b border-gray-800 backdrop-blur-lg bg-black/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <Users className="w-8 h-8 text-cyan-500" />
              <span className="text-xl font-bold text-white">Collaboration</span>
            </div>

            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/playground')}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-white transition"
              >
                <Brain className="w-4 h-4 inline mr-2" />
                Playground
              </button>
              <button
                onClick={() => router.push('/')}
                className="px-4 py-2 border border-gray-600 hover:border-gray-500 rounded-lg text-gray-300 transition"
              >
                <Home className="w-4 h-4 inline mr-2" />
                Home
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Collaboration Sessions</h1>
            <p className="text-gray-400">Work together on AI models and code</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 rounded-lg text-white font-medium transition flex items-center"
          >
            <Plus className="w-5 h-5 mr-2" />
            New Session
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-12">
            <Users className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">No active sessions</h2>
            <p className="text-gray-400 mb-6">Create a new collaboration session to get started</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 rounded-lg text-white font-medium transition"
            >
              Create Session
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sessions.map((session) => (
              <div
                key={session.id}
                className="bg-gray-800/50 border border-gray-700 rounded-lg p-6 hover:border-cyan-500 transition cursor-pointer"
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-1">{session.name}</h3>
                    {session.description && (
                      <p className="text-sm text-gray-400">{session.description}</p>
                    )}
                  </div>
                  {session.is_active && (
                    <CheckCircle className="w-5 h-5 text-green-400" />
                  )}
                </div>

                <div className="space-y-2 border-t border-gray-700 pt-4">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">Participants</span>
                    <span className="text-white font-medium">{session.participants?.length || 0}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">Shared Models</span>
                    <span className="text-white font-medium">{session.shared_models?.length || 0}</span>
                  </div>
                  <div className="flex items-center text-sm text-gray-400">
                    <Clock className="w-4 h-4 mr-1" />
                    {new Date(session.created_at).toLocaleDateString()}
                  </div>
                </div>

                <button className="w-full mt-4 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 rounded-lg text-white text-sm transition flex items-center justify-center">
                  <Share2 className="w-4 h-4 mr-2" />
                  Join Session
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Session Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur flex items-center justify-center p-4 z-50">
          <div className="bg-gray-800 rounded-2xl p-6 max-w-md w-full">
            <h3 className="text-xl font-bold text-white mb-4">Create Collaboration Session</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Session Name</label>
                <input
                  type="text"
                  value={newSessionName}
                  onChange={(e) => setNewSessionName(e.target.value)}
                  placeholder="Enter session name"
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Description (Optional)</label>
                <textarea
                  value={newSessionDesc}
                  onChange={(e) => setNewSessionDesc(e.target.value)}
                  placeholder="Enter description"
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-cyan-500 resize-none"
                  rows={3}
                />
              </div>
            </div>

            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white transition"
              >
                Cancel
              </button>
              <button
                onClick={createSession}
                disabled={!newSessionName.trim()}
                className="flex-1 px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 rounded-lg text-white transition disabled:opacity-50"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
