'use client'

import { useState } from 'react'
import { Upload, Link, Container, Cpu } from 'lucide-react'

type ModelType = 'sdk' | 'api' | 'container'

interface Model {
  id: string
  name: string
  type: ModelType
  status: 'running' | 'stopped' | 'error'
  createdAt: Date
}

export default function ModelManager() {
  const [models, setModels] = useState<Model[]>([])
  const [isUploading, setIsUploading] = useState(false)

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    // Upload logic here
    setTimeout(() => {
      setModels(prev => [...prev, {
        id: Math.random().toString(36),
        name: file.name,
        type: 'sdk',
        status: 'stopped',
        createdAt: new Date()
      }])
      setIsUploading(false)
    }, 2000)
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-lg font-semibold mb-4">Model Manager</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
          <input
            type="file"
            id="sdk-upload"
