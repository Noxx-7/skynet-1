'use client'

import { useState } from 'react'
import { AlertCircle, CheckCircle, Lightbulb, TrendingUp, Loader2, FileCode } from 'lucide-react'

interface CodeAnalysisSidebarProps {
  code: string
  onOptimize: () => void
}

interface Improvement {
  type: string
  severity: string
  message: string
  line: number | null
}

interface Analysis {
  complexity_score?: number
  lines_of_code?: number
  functions?: number
  classes?: number
  issues?: string[]
  suggestions?: string[]
}

export default function CodeAnalysisSidebar({ code, onOptimize }: CodeAnalysisSidebarProps) {
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [improvements, setImprovements] = useState<Improvement[]>([])
  const [loading, setLoading] = useState(false)
  const [showOptimized, setShowOptimized] = useState(false)

  const analyzeCode = async () => {
    if (!code.trim()) {
      return
    }

    setLoading(true)
    try {
      const [analysisRes, optimizationRes] = await Promise.all([
        fetch('http://localhost:8000/code/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code })
        }),
        fetch('http://localhost:8000/code/optimize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code, language: 'python' })
        })
      ])

      if (analysisRes.ok) {
        const analysisData = await analysisRes.json()
        setAnalysis(analysisData)
      }

      if (optimizationRes.ok) {
        const optimizationData = await optimizationRes.json()
        setImprovements(optimizationData.improvements || [])
      }
    } catch (err) {
      console.error('Error analyzing code:', err)
    } finally {
      setLoading(false)
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'medium':
        return 'text-orange-600 bg-orange-50 border-orange-200'
      case 'low':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return <AlertCircle className="w-4 h-4" />
      case 'medium':
        return <AlertCircle className="w-4 h-4" />
      case 'low':
        return <Lightbulb className="w-4 h-4" />
      default:
        return <CheckCircle className="w-4 h-4" />
    }
  }

  return (
    <div className="h-full bg-white border-l border-gray-200 flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <h3 className="font-semibold text-lg mb-2">Code Analysis</h3>
        <button
          onClick={analyzeCode}
          disabled={loading || !code.trim()}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <FileCode className="w-4 h-4 mr-2" />
              Analyze Code
            </>
          )}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {loading && (
          <div className="text-center py-8 text-gray-500">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2" />
            <p className="text-sm">Analyzing your code...</p>
          </div>
        )}

        {!loading && !analysis && (
          <div className="text-center py-8 text-gray-500">
            <FileCode className="w-12 h-12 mx-auto mb-2 text-gray-300" />
            <p className="text-sm">Click "Analyze Code" to get insights</p>
          </div>
        )}

        {!loading && analysis && (
          <>
            <div className="bg-gray-50 rounded-lg p-4 space-y-3">
              <h4 className="font-semibold text-sm text-gray-700 mb-2">Code Metrics</h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white rounded p-2">
                  <p className="text-xs text-gray-500">Lines of Code</p>
                  <p className="text-lg font-semibold">{analysis.lines_of_code || 0}</p>
                </div>
                <div className="bg-white rounded p-2">
                  <p className="text-xs text-gray-500">Complexity</p>
                  <p className={`text-lg font-semibold ${
                    (analysis.complexity_score || 0) > 10 ? 'text-red-600' : 'text-green-600'
                  }`}>
                    {analysis.complexity_score || 0}
                  </p>
                </div>
                <div className="bg-white rounded p-2">
                  <p className="text-xs text-gray-500">Functions</p>
                  <p className="text-lg font-semibold">{analysis.functions || 0}</p>
                </div>
                <div className="bg-white rounded p-2">
                  <p className="text-xs text-gray-500">Classes</p>
                  <p className="text-lg font-semibold">{analysis.classes || 0}</p>
                </div>
              </div>
            </div>

            {improvements.length > 0 && (
              <div>
                <h4 className="font-semibold text-sm text-gray-700 mb-3 flex items-center">
                  <TrendingUp className="w-4 h-4 mr-1" />
                  Improvement Suggestions
                </h4>
                <div className="space-y-2">
                  {improvements.map((improvement, idx) => (
                    <div
                      key={idx}
                      className={`border rounded-lg p-3 ${getSeverityColor(improvement.severity)}`}
                    >
                      <div className="flex items-start space-x-2">
                        <div className="flex-shrink-0 mt-0.5">
                          {getSeverityIcon(improvement.severity)}
                        </div>
                        <div className="flex-1">
                          <p className="text-xs font-medium capitalize mb-1">
                            {improvement.type.replace('_', ' ')}
                          </p>
                          <p className="text-xs">{improvement.message}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="border-t border-gray-200 pt-4">
              <button
                onClick={onOptimize}
                className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center justify-center"
              >
                <TrendingUp className="w-4 h-4 mr-2" />
                Generate Optimized Code
              </button>
              <p className="text-xs text-gray-500 mt-2 text-center">
                AI will generate a fully optimized version
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
