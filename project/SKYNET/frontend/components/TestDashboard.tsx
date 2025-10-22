'use client'

import { useState } from 'react'
import { Code } from 'lucide-react'
import TestResultsDashboard from './TestResultsDashboard'
import Editor from '@monaco-editor/react'

export default function TestDashboard() {
  const [code, setCode] = useState(`def add(a, b):
    """Add two numbers"""
    return a + b

def multiply(a, b):
    """Multiply two numbers"""
    return a * b

def fibonacci(n):
    """Generate Fibonacci sequence"""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]

    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib
`)
  const [testCode, setTestCode] = useState('')
  const [showCodeEditor, setShowCodeEditor] = useState(true)

  return (
    <div className="bg-white rounded-lg shadow-lg h-full flex flex-col">
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Test Dashboard</h2>
          <p className="text-sm text-gray-500">Write code and automatically generate & run tests</p>
        </div>
        <button
          onClick={() => setShowCodeEditor(!showCodeEditor)}
          className={`flex items-center px-4 py-2 rounded-lg transition-colors ${
            showCodeEditor
              ? 'bg-blue-100 text-blue-600'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <Code className="w-4 h-4 mr-2" />
          {showCodeEditor ? 'Hide Code' : 'Show Code'}
        </button>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {showCodeEditor && (
          <div className="w-1/2 border-r border-gray-200 flex flex-col">
            <div className="p-2 bg-gray-50 border-b border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700">Your Code</h3>
            </div>
            <div className="flex-1">
              <Editor
                height="100%"
                defaultLanguage="python"
                value={code}
                onChange={(value) => setCode(value || '')}
                options={{
                  minimap: { enabled: false },
                  fontSize: 13,
                  wordWrap: 'on',
                  automaticLayout: true,
                }}
              />
            </div>
          </div>
        )}

        <div className={showCodeEditor ? 'w-1/2' : 'w-full'}>
          <TestResultsDashboard code={code} testCode={testCode} />
        </div>
      </div>
    </div>
  )
}
