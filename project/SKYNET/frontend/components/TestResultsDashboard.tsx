'use client'

import { useState } from 'react'
import { CheckCircle, XCircle, Clock, AlertTriangle, PlayCircle, Loader2, Eye } from 'lucide-react'

interface TestResult {
  test_name: string
  passed: boolean
  error_message?: string
  execution_time?: number
}

interface TestResultsDashboardProps {
  code: string
  testCode: string
}

export default function TestResultsDashboard({ code, testCode }: TestResultsDashboardProps) {
  const [testResults, setTestResults] = useState<TestResult[]>([])
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState<{
    total: number
    passed: number
    failed: number
    executionTime: number
  } | null>(null)
  const [selectedTest, setSelectedTest] = useState<TestResult | null>(null)
  const [autoRunMode, setAutoRunMode] = useState(false)
  const [difficulty, setDifficulty] = useState<'low' | 'mid' | 'high'>('mid')

  const runTests = async () => {
    if (!code.trim()) return

    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/code/run-tests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code,
          test_code: testCode
        })
      })

      if (response.ok) {
        const data = await response.json()
        const results = data.test_results || []
        setTestResults(results)

        const passed = results.filter((t: TestResult) => t.passed).length
        const failed = results.length - passed
        const totalTime = results.reduce((sum: number, t: TestResult) => sum + (t.execution_time || 0), 0)

        setSummary({
          total: results.length,
          passed,
          failed,
          executionTime: totalTime
        })
      }
    } catch (err) {
      console.error('Error running tests:', err)
    } finally {
      setLoading(false)
    }
  }

  const runAutoTests = async () => {
    if (!code.trim()) return

    setLoading(true)
    setAutoRunMode(true)
    try {
      const response = await fetch('http://localhost:8000/code/run-auto-tests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code,
          difficulty
        })
      })

      if (response.ok) {
        const data = await response.json()
        const results = data.test_results || []
        setTestResults(results)

        setSummary({
          total: data.test_count || results.length,
          passed: data.passed || 0,
          failed: data.failed || 0,
          executionTime: results.reduce((sum: number, t: TestResult) => sum + (t.execution_time || 0), 0)
        })
      }
    } catch (err) {
      console.error('Error running auto tests:', err)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (passed: boolean) => {
    return passed ? 'text-green-600 bg-green-50' : 'text-red-600 bg-red-50'
  }

  return (
    <div className="h-full bg-white rounded-lg shadow-lg flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Test Results Dashboard</h2>
          <div className="flex items-center space-x-2">
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value as 'low' | 'mid' | 'high')}
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="low">Low (5 tests)</option>
              <option value="mid">Mid (15 tests)</option>
              <option value="high">High (25 tests)</option>
            </select>
            <button
              onClick={runAutoTests}
              disabled={loading || !code.trim()}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {loading && autoRunMode ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <PlayCircle className="w-4 h-4 mr-2" />
              )}
              Auto Generate & Run
            </button>
            <button
              onClick={runTests}
              disabled={loading || !code.trim() || !testCode.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {loading && !autoRunMode ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <PlayCircle className="w-4 h-4 mr-2" />
              )}
              Run Tests
            </button>
          </div>
        </div>

        {summary && (
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-500 mb-1">Total Tests</p>
              <p className="text-2xl font-bold">{summary.total}</p>
            </div>
            <div className="bg-green-50 rounded-lg p-3">
              <p className="text-xs text-green-600 mb-1">Passed</p>
              <p className="text-2xl font-bold text-green-600">{summary.passed}</p>
            </div>
            <div className="bg-red-50 rounded-lg p-3">
              <p className="text-xs text-red-600 mb-1">Failed</p>
              <p className="text-2xl font-bold text-red-600">{summary.failed}</p>
            </div>
            <div className="bg-blue-50 rounded-lg p-3">
              <p className="text-xs text-blue-600 mb-1">Success Rate</p>
              <p className="text-2xl font-bold text-blue-600">
                {summary.total > 0 ? Math.round((summary.passed / summary.total) * 100) : 0}%
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto">
        {loading && (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Loader2 className="w-12 h-12 animate-spin mb-4" />
            <p className="text-sm">Running tests...</p>
          </div>
        )}

        {!loading && testResults.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <PlayCircle className="w-16 h-16 mb-4 text-gray-300" />
            <p className="text-sm mb-2">No test results yet</p>
            <p className="text-xs text-gray-400">Click "Auto Generate & Run" or "Run Tests" to begin</p>
          </div>
        )}

        {!loading && testResults.length > 0 && (
          <div className="divide-y divide-gray-100">
            {testResults.map((test, idx) => (
              <div
                key={idx}
                className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                  selectedTest === test ? 'bg-blue-50' : ''
                }`}
                onClick={() => setSelectedTest(test)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    <div className={`mt-0.5 ${getStatusColor(test.passed)}`}>
                      {test.passed ? (
                        <CheckCircle className="w-5 h-5" />
                      ) : (
                        <XCircle className="w-5 h-5" />
                      )}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-sm text-gray-900">{test.test_name}</h4>
                      {test.error_message && (
                        <p className="text-xs text-red-600 mt-1 line-clamp-2">{test.error_message}</p>
                      )}
                      {test.execution_time && (
                        <div className="flex items-center text-xs text-gray-500 mt-1">
                          <Clock className="w-3 h-3 mr-1" />
                          {test.execution_time.toFixed(3)}s
                        </div>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      setSelectedTest(test)
                    }}
                    className="text-blue-600 hover:text-blue-700"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {selectedTest && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col">
            <div className="p-6 border-b border-gray-200 flex items-start justify-between">
              <div>
                <h3 className="text-xl font-semibold flex items-center">
                  <span className={`mr-2 ${getStatusColor(selectedTest.passed)}`}>
                    {selectedTest.passed ? (
                      <CheckCircle className="w-6 h-6" />
                    ) : (
                      <XCircle className="w-6 h-6" />
                    )}
                  </span>
                  {selectedTest.test_name}
                </h3>
                {selectedTest.execution_time && (
                  <p className="text-sm text-gray-500 mt-1 flex items-center">
                    <Clock className="w-4 h-4 mr-1" />
                    Execution time: {selectedTest.execution_time.toFixed(3)}s
                  </p>
                )}
              </div>
              <button
                onClick={() => setSelectedTest(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XCircle className="w-6 h-6" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold text-sm text-gray-700 mb-2">Status</h4>
                  <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                    selectedTest.passed
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {selectedTest.passed ? 'PASSED' : 'FAILED'}
                  </div>
                </div>

                {selectedTest.error_message && (
                  <div>
                    <h4 className="font-semibold text-sm text-gray-700 mb-2">Error Details</h4>
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <pre className="text-xs text-red-800 whitespace-pre-wrap font-mono">
                        {selectedTest.error_message}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="p-6 border-t border-gray-200 flex justify-end">
              <button
                onClick={() => setSelectedTest(null)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
