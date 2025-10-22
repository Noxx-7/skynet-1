'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { 
  Brain, Play, TestTube2, Zap, Save, Download, 
  Copy, Check, BarChart, Shield, Loader2, Code,
  FileText, ChevronRight, CheckCircle, XCircle,
  Clock, Activity, MemoryStick, Cpu, Home, MessageSquareText
} from 'lucide-react';

const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

interface TestResult {
  name: string;
  status: 'passed' | 'failed' | 'error';
  message?: string;
  execution_time?: number;
}

interface PerformanceMetrics {
  execution_time: number;
  memory_usage: number;
  cpu_usage: number;
  complexity_score?: number;
}

export default function CodeEditor() {
  const router = useRouter();
  const [code, setCode] = useState(`# Python Code Editor - No Login Required!
# Write your Python code here
# Auto unit tests will be generated when you run tests

def fibonacci(n):
    """Calculate the nth Fibonacci number"""
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)

# Test your code
print(fibonacci(10))
`);
  
  const [output, setOutput] = useState('');
  const [testCode, setTestCode] = useState('');
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingTests, setLoadingTests] = useState(false);
  const [loadingAISuggestion, setLoadingAISuggestion] = useState(false); // New state for AI suggestion loading
  const [aiSuggestion, setAiSuggestion] = useState(''); // New state for AI suggestion
  const [activeTab, setActiveTab] = useState<'output' | 'tests' | 'performance' | 'ai-suggestions'>('output'); // New tab for AI suggestions
  const [copied, setCopied] = useState(false);

  const handleRunCode = async () => {
    setLoading(true);
    setOutput('');
    setTestResults([]);
    setPerformanceMetrics(null);

    try {
      const response = await fetch('/api/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code })
      });

      const data = await response.json();
      
      if (data.success) {
        setOutput(data.output || 'Code executed successfully');
        if (data.test_results) {
          setTestResults(data.test_results);
        }
        if (data.execution_time || data.memory_usage || data.cpu_usage) {
          setPerformanceMetrics({
            execution_time: data.execution_time || 0,
            memory_usage: data.memory_usage || 0,
            cpu_usage: data.cpu_usage || 0,
            complexity_score: data.complexity_score
          });
        }
      } else {
        setOutput(`Error: ${data.error || 'Unknown error'}`);
      }
    } catch (error) {
      setOutput(`Failed to execute code: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateAISuggestion = async () => {
    setLoadingAISuggestion(true);
    setAiSuggestion('');
    setActiveTab('ai-suggestions');

    try {
      const response = await fetch('/api/code/suggest', { // Assuming a new API endpoint for AI suggestions
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code })
      });

      const data = await response.json();

      if (response.ok && data.suggestion) {
        setAiSuggestion(data.suggestion);
      } else {
        const errorMsg = data.error || data.detail || 'Unknown error occurred';
        setAiSuggestion(`Error generating AI suggestion: ${errorMsg}`);
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Network error';
      setAiSuggestion(`Failed to generate AI suggestion: ${errorMsg}`);
    } finally {
      setLoadingAISuggestion(false);
    }
  };

  const handleGenerateTests = async () => {
    setLoadingTests(true);

    try {
      const response = await fetch('/api/code/generate-tests', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code, difficulty: 'mid' })
      });

      const data = await response.json();

      if (response.ok && data.test_code) {
        setTestCode(data.test_code);
        setActiveTab('tests');
      } else {
        const errorMsg = data.error || data.detail || 'Unknown error occurred';
        setTestCode(`# Error generating tests: ${errorMsg}`);
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Network error';
      setTestCode(`# Failed to generate tests: ${errorMsg}`);
    } finally {
      setLoadingTests(false);
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
              <Code className="w-8 h-8 text-blue-500" />
              <span className="text-xl font-bold text-white">Python Code Editor</span>
              <span className="text-sm text-gray-400">(No Login Required)</span>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/playground')}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-white transition flex items-center"
              >
                <Brain className="w-4 h-4 mr-2" />
                Skynet Playground
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
        {/* Code Editor */}
        <div className="flex-1 flex flex-col border-r border-gray-800">
          <div className="p-4 bg-gray-900/50 border-b border-gray-800 flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <FileText className="w-5 h-5 text-blue-400" />
              <span className="text-white font-medium">main.py</span>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={handleGenerateAISuggestion}
                disabled={loadingAISuggestion}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm transition disabled:opacity-50 flex items-center"
              >
                {loadingAISuggestion ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Brain className="w-4 h-4 mr-2" />
                )}
                AI Suggestion
              </button>
              <button
                onClick={handleGenerateTests}
                disabled={loadingTests}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white text-sm transition disabled:opacity-50 flex items-center"
              >
                {loadingTests ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <TestTube2 className="w-4 h-4 mr-2" />
                )}
                Generate Tests
              </button>
              <button
                onClick={handleRunCode}
                disabled={loading}
                className="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 rounded-lg text-white font-medium transition disabled:opacity-50 flex items-center"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                ) : (
                  <Play className="w-5 h-5 mr-2" />
                )}
                Run Code
              </button>
            </div>
          </div>
          
          <div className="flex-1">
            <MonacoEditor
              height="100%"
              defaultLanguage="python"
              value={code}
              onChange={(value) => setCode(value || '')}
              theme="vs-dark"
              options={{
                minimap: { enabled: true },
                fontSize: 14,
                wordWrap: 'on',
                automaticLayout: true,
                scrollBeyondLastLine: false,
                padding: { top: 16, bottom: 16 }
              }}
            />
          </div>
        </div>

        {/* Output Panel */}
        <div className="w-96 flex flex-col bg-gray-900/30">
          {/* Tabs */}
          <div className="flex border-b border-gray-800 bg-gray-900/50">
            <button
              onClick={() => setActiveTab('output')}
              className={`flex-1 px-4 py-3 text-sm font-medium transition ${
                activeTab === 'output'
                  ? 'text-white bg-gray-800 border-b-2 border-blue-500'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
              }`}
            >
              <div className="flex items-center justify-center">
                <FileText className="w-4 h-4 mr-2" />
                Output
              </div>
            </button>
            <button
              onClick={() => setActiveTab('tests')}
              className={`flex-1 px-4 py-3 text-sm font-medium transition ${
                activeTab === 'tests'
                  ? 'text-white bg-gray-800 border-b-2 border-purple-500'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
              }`}
            >
              <div className="flex items-center justify-center">
                <TestTube2 className="w-4 h-4 mr-2" />
                Tests
              </div>
            </button>
            <button
              onClick={() => setActiveTab('performance')}
              className={`flex-1 px-4 py-3 text-sm font-medium transition ${
                activeTab === 'performance'
                  ? 'text-white bg-gray-800 border-b-2 border-green-500'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
              }`}
            >
              <div className="flex items-center justify-center">
                <BarChart className="w-4 h-4 mr-2" />
                Metrics
              </div>
            </button>
            <button
              onClick={() => setActiveTab('ai-suggestions')}
              className={`flex-1 px-4 py-3 text-sm font-medium transition ${
                activeTab === 'ai-suggestions'
                  ? 'text-white bg-gray-800 border-b-2 border-blue-500'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
              }`}
            >
              <div className="flex items-center justify-center">
                <Brain className="w-4 h-4 mr-2" />
                AI
              </div>
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto p-4">
            {activeTab === 'output' && (
              <div>
                {output ? (
                  <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-gray-400">Execution Result</span>
                      <button
                        onClick={() => copyToClipboard(output)}
                        className="text-gray-400 hover:text-white transition"
                      >
                        {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                      </button>
                    </div>
                    <pre className="text-white text-sm whitespace-pre-wrap font-mono">{output}</pre>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Play className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                    <p className="text-gray-400">Run your code to see output</p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'tests' && (
              <div>
                {testCode ? (
                  <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-gray-400">Generated Tests</span>
                      <button
                        onClick={() => copyToClipboard(testCode)}
                        className="text-gray-400 hover:text-white transition"
                      >
                        {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                      </button>
                    </div>
                    <pre className="text-white text-sm whitespace-pre-wrap font-mono">{testCode}</pre>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <TestTube2 className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                    <p className="text-gray-400">Click "Generate Tests" to create unit tests</p>
                  </div>
                )}

                {testResults.length > 0 && (
                  <div className="mt-4 space-y-2">
                    <h3 className="text-sm font-medium text-white mb-2">Test Results</h3>
                    {testResults.map((result, index) => (
                      <div
                        key={index}
                        className={`p-3 rounded-lg border ${
                      <div className="text-2xl font-bold text-white">
                        {performanceMetrics.cpu_usage.toFixed(1)}%
                      </div>
                    </div>

                    {performanceMetrics.complexity_score !== undefined && (
                      <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                        <div className="flex items-center mb-2">
                          <Activity className="w-4 h-4 text-yellow-400 mr-2" />
                          <span className="text-sm text-gray-400">Complexity Score</span>
                        </div>
                        <div className="text-2xl font-bold text-white">
                          {performanceMetrics.complexity_score}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <BarChart className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                    <p className="text-gray-400">Run your code to see performance metrics</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
