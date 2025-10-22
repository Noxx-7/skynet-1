'use client'

import { useState, useRef, useEffect } from 'react'
import Editor from '@monaco-editor/react'
import { useStore } from '@/lib/store'
import { Play, Save, Share2, FileUp, BarChart3, FlaskConical, CheckCircle, XCircle, Sparkles, Send, Loader2 } from 'lucide-react'
import CodeAnalysisSidebar from './CodeAnalysisSidebar'

export default function CodeEditor() {
  const [code, setCode] = useState('# Your Skynet SDK code here\n\nclass MySkynetModel:\n    def __init__(self):\n        self.name = "my-custom-model"\n    \n    def generate(self, prompt: str) -> str:\n        # Implement your model logic\n        return f"Response to: {prompt}"')
  const [isRunning, setIsRunning] = useState(false)
  const [showAnalysis, setShowAnalysis] = useState(false)
  const [optimizedCode, setOptimizedCode] = useState<string | null>(null)
  const [showOptimizedModal, setShowOptimizedModal] = useState(false)
  const [generatedTests, setGeneratedTests] = useState<string | null>(null)
  const [showTestModal, setShowTestModal] = useState(false)
  const [testResults, setTestResults] = useState<any[]>([])
  const [showTestResults, setShowTestResults] = useState(false)
  const [isGeneratingTests, setIsGeneratingTests] = useState(false)
  const [isRunningTests, setIsRunningTests] = useState(false)
  const editorRef = useRef<any>(null)
  const [showAIAssistant, setShowAIAssistant] = useState(false)
  const [aiInput, setAiInput] = useState('')
  const [aiMessages, setAiMessages] = useState<Array<{role: string, content: string}>>([])
  const [isAiLoading, setIsAiLoading] = useState(false)
  const [availableModels, setAvailableModels] = useState<any[]>([])
  const [selectedAiModel, setSelectedAiModel] = useState<string | null>(null)

  useEffect(() => {
    fetchAvailableModels()
  }, [])

  const fetchAvailableModels = async () => {
    try {
      const response = await fetch('http://localhost:8000/llm/api-keys')
      if (response.ok) {
        const apiKeys = await response.json()
        const modelsResponse = await fetch('http://localhost:8000/models/list')
        if (modelsResponse.ok) {
          const models = await modelsResponse.json()
          const filteredModels = models.filter((m: any) =>
            apiKeys.some((key: any) => key.provider === m.provider && key.is_active)
          )
          setAvailableModels(filteredModels)
          if (filteredModels.length > 0 && !selectedAiModel) {
            setSelectedAiModel(filteredModels[0].id)
          }
        }
      }
    } catch (err) {
      console.error('Error fetching models:', err)
    }
  }

  const handleRun = async () => {
    setIsRunning(true)
    try {
      console.log('Running code...')
    } catch (error) {
      console.error('Execution error:', error)
    } finally {
      setIsRunning(false)
    }
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const content = e.target?.result as string
        setCode(content)
      }
      reader.readAsText(file)
    }
  }

  const handleOptimize = async () => {
    try {
      const response = await fetch('http://localhost:8000/code/generate-optimized', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language: 'python' })
      })

      if (response.ok) {
        const data = await response.json()
        setOptimizedCode(data.optimized_code)
        setShowOptimizedModal(true)
      }
    } catch (err) {
      console.error('Error optimizing code:', err)
    }
  }

  const applyOptimizedCode = () => {
    if (optimizedCode) {
      setCode(optimizedCode)
      setShowOptimizedModal(false)
      setOptimizedCode(null)
    }
  }

  const handleGenerateTests = async () => {
    setIsGeneratingTests(true)
    try {
      const response = await fetch('http://localhost:8000/code/generate-tests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language: 'python', difficulty: 'mid' })
      })

      if (response.ok) {
        const data = await response.json()
        setGeneratedTests(data.test_code)
        setShowTestModal(true)
      }
    } catch (err) {
      console.error('Error generating tests:', err)
    } finally {
      setIsGeneratingTests(false)
    }
  }

  const handleRunTests = async () => {
    if (!generatedTests) return

    setIsRunningTests(true)
    try {
      const response = await fetch('http://localhost:8000/code/run-tests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, test_code: generatedTests })
      })

      if (response.ok) {
        const data = await response.json()
        setTestResults(data.test_results || [])
        setShowTestResults(true)
      }
    } catch (err) {
      console.error('Error running tests:', err)
    } finally {
      setIsRunningTests(false)
    }
  }

  const handleAiAssist = async () => {
    if (!aiInput.trim() || !selectedAiModel) return

    const userMessage = { role: 'user', content: aiInput }
    setAiMessages(prev => [...prev, userMessage])
    setAiInput('')
    setIsAiLoading(true)

    try {
      const contextPrompt = `You are a code assistant. The user is working on this code:\n\n${code}\n\nUser question: ${aiInput}\n\nProvide helpful suggestions, explanations, or code improvements.`

      const response = await fetch('http://localhost:8000/llm/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: contextPrompt,
          model_id: selectedAiModel,
          temperature: 0.7,
          max_tokens: 1000
        })
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setAiMessages(prev => [...prev, { role: 'assistant', content: data.response }])
        } else {
          setAiMessages(prev => [...prev, { role: 'assistant', content: `Error: ${data.error}` }])
        }
      }
    } catch (err) {
      console.error('Error calling AI:', err)
      setAiMessages(prev => [...prev, { role: 'assistant', content: 'Failed to get AI response' }])
    } finally {
      setIsAiLoading(false)
    }
  }

  const applyAiSuggestion = (suggestion: string) => {
    const codeMatch = suggestion.match(/```(?:python|javascript|typescript)?\n([\s\S]*?)```/)
    if (codeMatch) {
      setCode(codeMatch[1].trim())
    }
  }

  return (
    <>
      <div className="bg-white rounded-lg shadow-lg h-full flex">
        <div className="flex-1 flex flex-col">
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold">Code Editor</h2>
            <div className="flex space-x-2">
              <label className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 cursor-pointer">
                <FileUp className="w-4 h-4 mr-2" />
                Upload
                <input
                  type="file"
                  accept=".py,.js,.ts,.txt"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
              <button
                onClick={() => setShowAIAssistant(!showAIAssistant)}
                className={`flex items-center px-4 py-2 rounded-lg transition-colors ${
                  showAIAssistant
                    ? 'bg-purple-100 text-purple-600'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <Sparkles className="w-4 h-4 mr-2" />
                AI Assistant
              </button>
              <button
                onClick={() => setShowAnalysis(!showAnalysis)}
                className={`flex items-center px-4 py-2 rounded-lg transition-colors ${
                  showAnalysis
                    ? 'bg-blue-100 text-blue-600'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <BarChart3 className="w-4 h-4 mr-2" />
                Analysis
              </button>
              <button
                onClick={handleRun}
                disabled={isRunning}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                <Play className="w-4 h-4 mr-2" />
                {isRunning ? 'Running...' : 'Run'}
              </button>
              <button
                onClick={handleGenerateTests}
                disabled={isGeneratingTests}
                className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
              >
                <FlaskConical className="w-4 h-4 mr-2" />
                {isGeneratingTests ? 'Generating...' : 'Generate Tests'}
              </button>
              <button className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                <Save className="w-4 h-4 mr-2" />
                Save
              </button>
              <button className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
                <Share2 className="w-4 h-4 mr-2" />
                Share
              </button>
            </div>
          </div>

          <div className="flex-1">
            <Editor
              height="100%"
              defaultLanguage="python"
              value={code}
              onChange={(value) => setCode(value || '')}
              onMount={(editor) => (editorRef.current = editor)}
              options={{
                minimap: { enabled: true },
                fontSize: 14,
                wordWrap: 'on',
                automaticLayout: true,
              }}
            />
          </div>
        </div>

        {showAIAssistant && (
          <div className="w-96 flex-shrink-0 border-l border-gray-200 flex flex-col bg-gray-50">
            <div className="p-4 border-b border-gray-200 bg-white">
              <h3 className="text-lg font-semibold flex items-center">
                <Sparkles className="w-5 h-5 mr-2 text-purple-600" />
                AI Code Assistant
              </h3>
              {availableModels.length > 0 && (
                <select
                  value={selectedAiModel || ''}
                  onChange={(e) => setSelectedAiModel(e.target.value)}
                  className="mt-2 w-full border border-gray-300 rounded px-2 py-1 text-sm"
                >
                  {availableModels.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.name}
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {aiMessages.length === 0 ? (
                <div className="text-center text-gray-500 mt-8">
                  <Sparkles className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p className="text-sm">Ask me anything about your code!</p>
                  <div className="mt-4 text-xs text-left space-y-2 bg-white p-3 rounded-lg">
                    <p className="font-semibold">Try asking:</p>
                    <ul className="list-disc list-inside space-y-1 text-gray-600">
                      <li>Explain this code</li>
                      <li>How can I optimize this?</li>
                      <li>Add error handling</li>
                      <li>Refactor this function</li>
                    </ul>
                  </div>
                </div>
              ) : (
                aiMessages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`rounded-lg p-3 ${
                      msg.role === 'user'
                        ? 'bg-purple-100 ml-8'
                        : 'bg-white border border-gray-200 mr-8'
                    }`}
                  >
                    <div className="text-xs font-semibold mb-1 text-gray-600">
                      {msg.role === 'user' ? 'You' : 'AI Assistant'}
                    </div>
                    <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                    {msg.role === 'assistant' && msg.content.includes('```') && (
                      <button
                        onClick={() => applyAiSuggestion(msg.content)}
                        className="mt-2 text-xs px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700"
                      >
                        Apply Code
                      </button>
                    )}
                  </div>
                ))
              )}
              {isAiLoading && (
                <div className="bg-white border border-gray-200 rounded-lg p-3 mr-8">
                  <Loader2 className="w-4 h-4 text-purple-600 animate-spin" />
                </div>
              )}
            </div>

            <div className="p-4 border-t border-gray-200 bg-white">
              {availableModels.length === 0 ? (
                <p className="text-xs text-gray-500">No AI models available. Please configure API keys.</p>
              ) : (
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={aiInput}
                    onChange={(e) => setAiInput(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        handleAiAssist()
                      }
                    }}
                    placeholder="Ask about your code..."
                    className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                  <button
                    onClick={handleAiAssist}
                    disabled={!aiInput.trim() || isAiLoading}
                    className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {showAnalysis && (
          <div className="w-96 flex-shrink-0">
            <CodeAnalysisSidebar code={code} onOptimize={handleOptimize} />
          </div>
        )}
      </div>

      {showOptimizedModal && optimizedCode && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] flex flex-col">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-xl font-semibold">Optimized Code</h3>
              <p className="text-sm text-gray-500 mt-1">
                Review the optimized version and apply if you like it
              </p>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <pre className="text-sm whitespace-pre-wrap font-mono">{optimizedCode}</pre>
              </div>
            </div>

            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowOptimizedModal(false)
                  setOptimizedCode(null)
                }}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={applyOptimizedCode}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Apply Optimized Code
              </button>
            </div>
          </div>
        </div>
      )}

      {showTestModal && generatedTests && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] flex flex-col">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-xl font-semibold flex items-center">
                <FlaskConical className="w-6 h-6 mr-2 text-purple-600" />
                Generated Unit Tests
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                Review the generated tests and run them to verify your code
              </p>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <pre className="text-sm whitespace-pre-wrap font-mono">{generatedTests}</pre>
              </div>
            </div>

            <div className="p-6 border-t border-gray-200 flex justify-between items-center">
              <button
                onClick={() => {
                  setShowTestModal(false)
                }}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                Close
              </button>
              <div className="flex space-x-3">
                <button
                  onClick={handleRunTests}
                  disabled={isRunningTests}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center"
                >
                  <Play className="w-4 h-4 mr-2" />
                  {isRunningTests ? 'Running Tests...' : 'Run Tests'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showTestResults && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] flex flex-col">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-xl font-semibold">Test Results</h3>
              <p className="text-sm text-gray-500 mt-1">
                {testResults.filter(t => t.passed).length} of {testResults.length} tests passed
              </p>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              <div className="space-y-3">
                {testResults.map((result, idx) => (
                  <div
                    key={idx}
                    className={`border rounded-lg p-4 ${
                      result.passed ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-2 flex-1">
                        {result.passed ? (
                          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        ) : (
                          <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                        )}
                        <div className="flex-1">
                          <p className="font-medium text-sm">{result.test_name || `Test ${idx + 1}`}</p>
                          {result.error && (
                            <p className="text-xs text-red-700 mt-1 font-mono">{result.error}</p>
                          )}
                          {result.output && (
                            <p className="text-xs text-gray-600 mt-1">{result.output}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-6 border-t border-gray-200 flex justify-end">
              <button
                onClick={() => setShowTestResults(false)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
