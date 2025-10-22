'use client'

import { useStore } from '@/lib/store'
import { Code, TestTube, Cpu, MessageCircle, Users } from 'lucide-react'

const menuItems = [
  { id: 'code', label: 'Code Editor', icon: Code },
  { id: 'tests', label: 'Test Dashboard', icon: TestTube },
  { id: 'models', label: 'Model Manager', icon: Cpu },
  { id: 'chat', label: 'Chat Interface', icon: MessageCircle },
]

export default function Sidebar() {
  const { activeTab, setActiveTab } = useStore()

  return (
    <div className="w-64 bg-white border-r border-gray-200 h-full">
      <div className="p-6">
        <h2 className="text-lg font-semibold text-gray-800">Skynet Playground</h2>
      </div>
      
      <nav className="mt-6">
        {menuItems.map((item) => {
          const Icon = item.icon
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center px-6 py-3 text-left transition-colors ${
                activeTab === item.id
                  ? 'bg-blue-50 text-blue-600 border-r-2 border-blue-600'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Icon className="w-5 h-5 mr-3" />
              {item.label}
            </button>
          )
        })}
      </nav>
    </div>
  )
}