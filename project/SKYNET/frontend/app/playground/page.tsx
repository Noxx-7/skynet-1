'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Brain, Send, Upload, Settings, Plus, X, Loader2,
  Sparkles, Code, Copy, Check, Download, Share2,
  ChevronDown, FileText, Cpu, Zap, Home, History as HistoryIcon
} from 'lucide-react';
import ChatHistory from '@/components/ChatHistory';

interface Model {
  id: string;
  name: string;
  provider: string;
  type: string;
  description?: string;
  available?: boolean;
  checking?: boolean;
}

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

export default function Playground() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [availableModels, setAvailableModels] = useState<any>({});
  const [showModelUpload, setShowModelUpload] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(1000);
  const [apiKeys, setApiKeys] = useState<any>({});
  const [copied, setCopied] = useState(false);
  const [modelHealthStatus, setModelHealthStatus] = useState<Record<string, boolean>>({});
  const [checkingModels, setCheckingModels] = useState(false);
  const [sessionId, setSessionId] = useState<string>(() => Date.now().toString());
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    fetchModels();
    fetchAvailableModels();
    fetchApiKeys();
  }, []);

  // Check model health when API keys change
  useEffect(() => {
    if (Object.keys(apiKeys).length > 0 && models.length > 0) {
      checkModelHealth();
    }
  }, [apiKeys, models.length]);

  // Filter models to only show those with configured API keys and working
  const filteredModels = models.filter(model => {
    if (model.type === 'custom') return true; // Always show custom models
    if (!apiKeys[model.provider]) return false; // Hide if no API key
    // Show if checking or confirmed available
    return model.checking || modelHealthStatus[model.id] !== false;
  });

  // Update selected model when filtered models change
  useEffect(() => {
    if (filteredModels.length > 0) {
      // If current selected model is not in filtered list, switch to first filtered model
      if (!selectedModel || !filteredModels.find(m => m.id === selectedModel.id)) {
        setSelectedModel(filteredModels[0]);
        setMessages([]); // Clear messages when auto-switching
      }
    } else {
      setSelectedModel(null);
      setMessages([]);
    }
  }, [filteredModels.length, apiKeys]);

  // Handle model selection and clear chat history
  const handleSelectModel = (model: Model) => {
    setSelectedModel(model);
    setMessages([]); // Clear chat history when switching models
  };

  const fetchModels = async () => {
    try {
      const response = await fetch('/api/models');
      if (response.ok) {
        const allModels = await response.json();
        console.log('Fetched models:', allModels);
        setModels(allModels);
      } else {
        console.error('Failed to fetch models, status:', response.status);
        const errorText = await response.text();
        console.error('Error response:', errorText);
      }
    } catch (error) {
      console.error('Failed to fetch models:', error);
    }
  };

  const fetchAvailableModels = async () => {
    try {
      const response = await fetch('/api/llm/available-models');
      if (response.ok) {
        const data = await response.json();
        setAvailableModels(data);
      }
    } catch (error) {
      console.error('Failed to fetch available models:', error);
    }
  };

  const fetchApiKeys = async () => {
    try {
      const response = await fetch('/api/llm/api-keys');
      if (response.ok) {
        const data = await response.json();
        console.log('Fetched API keys:', data);
        const keysMap: any = {};
        data.forEach((key: any) => {
          keysMap[key.provider] = key;
        });
        setApiKeys(keysMap);
        console.log('API keys map:', keysMap);
      }
    } catch (error) {
      console.error('Failed to fetch API keys:', error);
    }
  };

  const checkModelHealth = async () => {
    setCheckingModels(true);
    const healthResults: Record<string, boolean> = {};

    // Check health for each model that has an API key
    const checkPromises = models
      .filter(model => model.type !== 'custom' && apiKeys[model.provider])
      .map(async (model) => {
        try {
          const response = await fetch('/api/llm/check-model-health', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              provider: model.provider,
              model_id: model.id.replace(`${model.provider}-`, '')
            })
          });

          if (response.ok) {
            const data = await response.json();
            healthResults[model.id] = data.available === true;
          } else {
            healthResults[model.id] = false;
          }
        } catch (error) {
          console.error(`Failed to check health for ${model.id}:`, error);
          healthResults[model.id] = false;
        }
      });

    await Promise.all(checkPromises);
    setModelHealthStatus(healthResults);
    setCheckingModels(false);
  };

  const handleSendMessage = async () => {
    if (!input.trim() || !selectedModel) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('/api/llm/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          prompt: input,
          model_id: selectedModel.id,
          temperature,
          max_tokens: maxTokens,
          stream: false
        })
      });

      const data = await response.json();
      
      if (response.ok && data.success) {
        const assistantMessage: Message = {
          role: 'assistant',
          content: data.response,
          timestamp: new Date()
        };
        const finalMessages = [...updatedMessages, assistantMessage];
        setMessages(finalMessages);
        await saveChatHistory(finalMessages);
      } else {
        const errorMessage: Message = {
          role: 'assistant',
          content: `Error: ${data.error || 'Failed to generate response. Please configure API keys for the model provider.'}`,
          timestamp: new Date()
        };
        const finalMessages = [...updatedMessages, errorMessage];
        setMessages(finalMessages);
        await saveChatHistory(finalMessages);
      }
    } catch (error) {
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Failed to connect to the model. Please check your connection and try again.',
        timestamp: new Date()
      };
      const finalMessages = [...updatedMessages, errorMessage];
      setMessages(finalMessages);
      await saveChatHistory(finalMessages);
    } finally {
      setLoading(false);
    }
  };

  const saveChatHistory = async (messagesToSave: Message[]) => {
    if (!selectedModel || messagesToSave.length === 0) return;

    try {
      await fetch('/api/chat-history', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          model_id: selectedModel.id,
          model_name: selectedModel.name,
          messages: messagesToSave.map(m => ({
            role: m.role,
            content: m.content,
            timestamp: m.timestamp.toISOString()
          })),
          title: messagesToSave[0]?.content.slice(0, 50) || 'New Chat'
        })
      });
    } catch (err) {
      console.error('Error saving chat history:', err);
    }
  };

  const loadChat = (loadedSessionId: string, loadedMessages: any[]) => {
    setSessionId(loadedSessionId);
    setMessages(
      loadedMessages.map((m: any) => ({
        role: m.role,
        content: m.content,
        timestamp: new Date(m.timestamp)
      }))
    );
    setShowHistory(false);
  };

  const startNewChat = () => {
    setSessionId(Date.now().toString());
    setMessages([]);
  };

  const handleModelUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', file.name.replace(/\.[^/.]+$/, ''));
    formData.append('type', 'custom');

    try {
      const response = await fetch('/api/models/upload', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        await fetchModels();
        setShowModelUpload(false);
      }
    } catch (error) {
      console.error('Failed to upload model:', error);
    }
  };

  const handleAddApiKey = async (provider: string, apiKey: string) => {
    try {
      const response = await fetch('/api/llm/api-keys', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          provider,
          api_key: apiKey
        })
      });

      if (response.ok) {
        await fetchApiKeys();
        await fetchModels();
        alert(`API key for ${provider} added successfully! Models are now available.`);
      } else {
        const errorData = await response.json();
        alert(`Failed to add API key: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Failed to add API key:', error);
      alert('Failed to add API key');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900">
      {/* Header */}
      <header className="border-b border-gray-800 backdrop-blur-lg bg-black/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <Brain className="w-8 h-8 text-purple-500" />
              <span className="text-xl font-bold text-white">Skynet Playground</span>
              <span className="text-sm text-gray-400">(No Login Required)</span>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowHistory(!showHistory)}
                className={`p-2 transition ${
                  showHistory ? 'text-purple-500' : 'text-gray-400 hover:text-white'
                }`}
                title="Chat History"
              >
                <HistoryIcon className="w-5 h-5" />
              </button>
              <button
                onClick={startNewChat}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-white transition text-sm"
              >
                New Chat
              </button>
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 text-gray-400 hover:text-white transition"
              >
                <Settings className="w-5 h-5" />
              </button>
              <button
                onClick={() => router.push('/code-editor')}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-white transition flex items-center"
              >
                <Code className="w-4 h-4 mr-2" />
                Code Editor
              </button>
              <button
                onClick={() => router.push('/')}
                className="px-4 py-2 border border-gray-600 hover:border-gray-500 rounded-lg text-gray-300 transition flex items-center"
              >
                <Home className="w-4 h-4 mr-2" />
                Home
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex h-[calc(100vh-4rem)]">
        {/* Chat History Sidebar */}
        {showHistory && (
          <div className="w-80 flex-shrink-0 bg-gray-900 border-r border-gray-800">
            <ChatHistory onLoadChat={loadChat} currentSessionId={sessionId} />
          </div>
        )}

        {/* Sidebar */}
        <div className="w-80 border-r border-gray-800 bg-gray-900/50 p-4 overflow-y-auto">
          {/* Model Selection */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-white">Models</h3>
              <button
                onClick={() => setShowModelUpload(true)}
                className="p-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white transition"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            
            <div className="space-y-2">
              {filteredModels.map((model) => {
                const isChecking = checkingModels && model.type !== 'custom';
                const isAvailable = model.type === 'custom' || modelHealthStatus[model.id] === true;
                const isUnavailable = modelHealthStatus[model.id] === false;

                return (
                  <button
                    key={model.id}
                    onClick={() => handleSelectModel(model)}
                    disabled={isUnavailable}
                    className={`w-full p-3 rounded-lg text-left transition ${
                      selectedModel?.id === model.id
                        ? 'bg-purple-600/20 border border-purple-500'
                        : isUnavailable
                        ? 'bg-gray-800/30 border border-gray-700 opacity-50 cursor-not-allowed'
                        : 'bg-gray-800/50 hover:bg-gray-800 border border-gray-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="text-white font-medium flex items-center">
                          {model.name}
                          {isChecking && (
                            <Loader2 className="w-3 h-3 ml-2 text-gray-400 animate-spin" />
                          )}
                        </div>
                        <div className="text-xs text-gray-400">{model.provider || 'Custom'}</div>
                        {isUnavailable && (
                          <div className="text-xs text-red-400 mt-1">Unavailable</div>
                        )}
                        {isAvailable && !isChecking && model.type !== 'custom' && (
                          <div className="text-xs text-green-400 mt-1">✓ Available</div>
                        )}
                      </div>
                      {model.type === 'custom' && (
                        <Cpu className="w-4 h-4 text-purple-400" />
                      )}
                      {isAvailable && model.type !== 'custom' && (
                        <Zap className="w-4 h-4 text-green-400" />
                      )}
                    </div>
                  </button>
                );
              })}
              
              {filteredModels.length === 0 && (
                <div className="text-gray-400 text-center py-8">
                  <Cpu className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>No models available</p>
                  <p className="text-sm mt-2">Configure API keys below to see available models</p>
                </div>
              )}
            </div>
          </div>

          {/* Quick Add API Models */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-white mb-4">Configure API Providers</h3>
            <div className="space-y-2">
              {Object.entries(availableModels).map(([provider, models]: [string, any]) => (
                <div key={provider} className="bg-gray-800/30 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-300 capitalize">{provider}</span>
                    {!apiKeys[provider] ? (
                      <button
                        onClick={() => {
                          const key = prompt(`Enter your ${provider} API key:`);
                          if (key) handleAddApiKey(provider, key);
                        }}
                        className="text-xs px-2 py-1 bg-purple-600 hover:bg-purple-700 rounded text-white"
                      >
                        Add Key
                      </button>
                    ) : (
                      <button
                        onClick={() => {
                          const key = prompt(`Update your ${provider} API key:`);
                          if (key) handleAddApiKey(provider, key);
                        }}
                        className="text-xs px-2 py-1 bg-green-600 hover:bg-green-700 rounded text-white"
                      >
                        Update Key
                      </button>
                    )}
                  </div>
                  {apiKeys[provider] && (
                    <div className="text-xs text-green-400">✓ API Key Configured</div>
                  )}
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-3">
              Note: API keys are stored locally for this session
            </p>
          </div>

          {/* Settings Panel */}
          {showSettings && (
            <div className="bg-gray-800/30 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-white mb-4">Settings</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">
                    Temperature: {temperature}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="2"
                    step="0.1"
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-gray-400 mb-2">
                    Max Tokens: {maxTokens}
                  </label>
                  <input
                    type="range"
                    min="100"
                    max="4000"
                    step="100"
                    value={maxTokens}
                    onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                    className="w-full"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6">
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Sparkles className="w-16 h-16 text-purple-500 mx-auto mb-4" />
                  <h2 className="text-2xl font-bold text-white mb-2">Start a Conversation</h2>
                  <p className="text-gray-400 mb-4">Choose a model and send your first message</p>
                  <div className="text-sm text-gray-500">
                    <p>1. Configure API keys in the sidebar (optional)</p>
                    <p>2. Select or upload a model</p>
                    <p>3. Start chatting!</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-4 max-w-4xl mx-auto">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[70%] rounded-lg p-4 ${
                        message.role === 'user'
                          ? 'bg-purple-600/20 border border-purple-500/50'
                          : 'bg-gray-800/50 border border-gray-700'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <span className="text-xs text-gray-400">
                          {message.role === 'user' ? 'You' : selectedModel?.name || 'Assistant'}
                        </span>
                        <button
                          onClick={() => copyToClipboard(message.content)}
                          className="ml-2 text-gray-400 hover:text-white transition"
                        >
                          {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                        </button>
                      </div>
                      <div className="text-white whitespace-pre-wrap">{message.content}</div>
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
                      <Loader2 className="w-5 h-5 text-purple-500 animate-spin" />
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-800 p-4">
            <div className="max-w-4xl mx-auto">
              <div className="flex items-end space-x-4">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  placeholder={selectedModel ? "Type your message..." : "Select a model first..."}
                  className="flex-1 bg-gray-800/50 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-purple-500 resize-none"
                  rows={3}
                  disabled={!selectedModel || loading}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!selectedModel || loading || !input.trim()}
                  className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 rounded-lg text-white font-medium transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {loading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <>
                      <Send className="w-5 h-5 mr-2" />
                      Send
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Model Upload Modal */}
      {showModelUpload && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur flex items-center justify-center p-4 z-50">
          <div className="bg-gray-800 rounded-2xl p-6 max-w-md w-full">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-white">Upload Custom Model</h3>
              <button
                onClick={() => setShowModelUpload(false)}
                className="text-gray-400 hover:text-white transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center">
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-300 mb-2">Drop your model SDK file here</p>
              <p className="text-sm text-gray-500 mb-4">or</p>
              <input
                type="file"
                onChange={(e) => {
                  if (e.target.files?.[0]) {
                    handleModelUpload(e.target.files[0]);
                  }
                }}
                className="hidden"
                id="model-upload"
                accept=".py,.js,.json"
              />
              <label
                htmlFor="model-upload"
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white cursor-pointer inline-block transition"
              >
                Browse Files
              </label>
            </div>
            
            <p className="text-xs text-gray-500 mt-4">
              Supported formats: Python SDK (.py), JavaScript SDK (.js), Model Config (.json)
            </p>
          </div>
        </div>
      )}
    </div>
  );
}