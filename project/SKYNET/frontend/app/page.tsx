'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  Code, 
  Brain, 
  Users, 
  Zap, 
  Upload, 
  Cpu, 
  TestTube2,
  Play,
  Sparkles,
  Shield,
  Rocket,
  BarChart,
  Moon,
  Sun
} from 'lucide-react';

export default function Home() {
  const [darkMode, setDarkMode] = useState(true);

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      setDarkMode(savedTheme === 'dark');
    }
  }, []);

  const toggleTheme = () => {
    const newMode = !darkMode;
    setDarkMode(newMode);
    localStorage.setItem('theme', newMode ? 'dark' : 'light');
  };
  const features = [
    {
      icon: Brain,
      title: "Multi-Skynet Support",
      description: "Use OpenAI, Claude, Gemini, or upload your custom models",
      color: "from-[#862633] to-[#a83245]"
    },
    {
      icon: Upload,
      title: "Custom Model Upload",
      description: "Drop your model SDK file and start testing immediately",
      color: "from-[#862633] to-[#6d1e28]"
    },
    {
      icon: Code,
      title: "Python Code Editor",
      description: "Write, test, and debug any Python code with auto unit tests",
      color: "from-[#a83245] to-[#c44857]"
    },
    {
      icon: TestTube2,
      title: "Auto Test Generation",
      description: "Automatically generate unit tests and performance profiles",
      color: "from-[#862633] to-[#a83245]"
    },
    {
      icon: Users,
      title: "Real-time Collaboration",
      description: "Work together with your team on models and code",
      color: "from-[#6d1e28] to-[#862633]"
    },
    {
      icon: BarChart,
      title: "Model Benchmarking",
      description: "Compare and benchmark different models side by side",
      color: "from-[#a83245] to-[#862633]"
    }
  ];

  const quickActions = [
    {
      title: "Skynet Playground",
      description: "Test and interact with AI models",
      icon: Sparkles,
      href: "/playground",
      gradient: "from-[#862633] to-[#a83245]"
    },
    {
      title: "Code Editor",
      description: "Write and test Python code",
      icon: Code,
      href: "/code-editor",
      gradient: "from-[#6d1e28] to-[#862633]"
    },
    {
      title: "Model Manager",
      description: "Upload and manage your models",
      icon: Cpu,
      href: "/models",
      gradient: "from-[#a83245] to-[#c44857]"
    },
    {
      title: "Collaborate",
      description: "Join or create sessions",
      icon: Users,
      href: "/collaborate",
      gradient: "from-[#862633] to-[#6d1e28]"
    }
  ];

  return (
    <div className={`min-h-screen transition-colors ${darkMode ? 'bg-gradient-to-br from-gray-900 via-black to-gray-900' : 'bg-gradient-to-br from-gray-50 via-white to-gray-100'}`}>
      {/* Navigation */}
      <nav className={`border-b backdrop-blur-lg ${darkMode ? 'border-gray-800 bg-black/50' : 'border-gray-200 bg-white/50'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-2">
              <img src="/skynet-logo.jpg" alt="Axis Skynet Logo" className="w-8 h-8 object-contain" />
              <span className={`text-xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                Axis Skynet
              </span>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={toggleTheme}
                className={`p-2 rounded-lg transition ${darkMode ? 'bg-gray-800 hover:bg-gray-700 text-yellow-400' : 'bg-gray-200 hover:bg-gray-300 text-gray-700'}`}
                aria-label="Toggle theme"
              >
                {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
              <Link
                href="/playground"
                className="px-4 py-2 bg-[#862633] hover:bg-[#6d1e28] rounded-lg text-white transition"
              >
                Launch Playground
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative py-20 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <div className={`inline-flex items-center justify-center p-2 rounded-full mb-6 ${darkMode ? 'bg-[#862633]/10' : 'bg-[#862633]/5'}`}>
            <Rocket className="w-5 h-5 text-[#862633] mr-2" />
            <span className="text-[#862633] text-sm font-medium">No GPU Required • Cloud-Based • No Login Needed</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold mb-6">
            <span className="bg-gradient-to-r from-[#862633] via-[#a83245] to-[#c44857] bg-clip-text text-transparent">
              Your Complete Skynet
            </span>
            <br />
            <span className={darkMode ? 'text-white' : 'text-gray-900'}>Development Platform</span>
          </h1>
          
          <p className={`text-xl max-w-3xl mx-auto mb-12 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Upload custom models, test with leading AI providers, write Python code with auto-testing, 
            and collaborate in real-time. No high-performance hardware or login needed.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/playground"
              className="px-8 py-4 bg-[#862633] hover:bg-[#6d1e28] rounded-xl text-white font-medium text-lg transition transform hover:scale-105 inline-flex items-center"
            >
              <Play className="w-5 h-5 mr-2" />
              Start Building Now
            </Link>
            <Link
              href="/code-editor"
              className={`px-8 py-4 rounded-xl font-medium text-lg transition transform hover:scale-105 inline-flex items-center ${darkMode ? 'bg-gray-800 hover:bg-gray-700 text-white' : 'bg-gray-200 hover:bg-gray-300 text-gray-900'}`}
            >
              <Code className="w-5 h-5 mr-2" />
              Open Code Editor
            </Link>
          </div>
        </div>

        {/* Animated gradient orbs */}
        <div className="absolute top-20 left-10 w-72 h-72 bg-[#862633] rounded-full filter blur-3xl opacity-20 animate-pulse"></div>
        <div className="absolute bottom-20 right-10 w-72 h-72 bg-[#a83245] rounded-full filter blur-3xl opacity-20 animate-pulse delay-1000"></div>
      </section>

      {/* Quick Actions */}
      <section className="py-16 px-4">
        <div className="max-w-7xl mx-auto">
          <h2 className={`text-3xl font-bold text-center mb-12 ${darkMode ? 'text-white' : 'text-gray-900'}`}>Quick Actions - No Login Required</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {quickActions.map((action, idx) => (
              <Link
                key={idx}
                href={action.href}
                className={`group relative overflow-hidden rounded-xl backdrop-blur border p-6 transition-all hover:scale-105 ${darkMode ? 'bg-gray-800/50 border-gray-700 hover:border-gray-600' : 'bg-white/50 border-gray-300 hover:border-gray-400'}`}
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${action.gradient} opacity-0 group-hover:opacity-10 transition-opacity`}></div>
                <action.icon className={`w-10 h-10 mb-4 bg-gradient-to-br ${action.gradient} bg-clip-text text-transparent`} />
                <h3 className={`text-xl font-semibold mb-2 ${darkMode ? 'text-white' : 'text-gray-900'}`}>{action.title}</h3>
                <p className={darkMode ? 'text-gray-400' : 'text-gray-600'}>{action.description}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-16 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className={`text-3xl md:text-4xl font-bold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              Everything You Need in One Platform
            </h2>
            <p className={`text-lg ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Build, test, and deploy AI applications without infrastructure hassles
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, idx) => (
              <div
                key={idx}
                className={`relative group overflow-hidden rounded-2xl backdrop-blur border p-8 transition-all ${darkMode ? 'bg-gray-800/30 border-gray-700 hover:border-gray-600' : 'bg-white/30 border-gray-300 hover:border-gray-400'}`}
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-5 transition-opacity`}></div>
                <div className={`inline-flex p-3 rounded-lg bg-gradient-to-br ${feature.color} mb-4`}>
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className={`text-xl font-semibold mb-3 ${darkMode ? 'text-white' : 'text-gray-900'}`}>{feature.title}</h3>
                <p className={darkMode ? 'text-gray-400' : 'text-gray-600'}>{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className={`backdrop-blur rounded-3xl p-12 border ${darkMode ? 'bg-gradient-to-r from-[#862633]/20 to-[#a83245]/20 border-[#862633]/20' : 'bg-gradient-to-r from-[#862633]/10 to-[#a83245]/10 border-[#862633]/30'}`}>
            <Shield className="w-16 h-16 mx-auto mb-6 text-[#862633]" />
            <h2 className={`text-3xl md:text-4xl font-bold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              Ready to Build with AI?
            </h2>
            <p className={`text-lg mb-8 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
              Start building immediately - no registration, no credit card, no hassle.
              Everything is ready for you!
            </p>
            <Link
              href="/playground"
              className="inline-flex items-center px-8 py-4 bg-[#862633] hover:bg-[#6d1e28] rounded-xl text-white font-medium text-lg transition transform hover:scale-105"
            >
              <Sparkles className="w-5 h-5 mr-2" />
              Launch Playground Now
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className={`border-t py-8 px-4 ${darkMode ? 'border-gray-800' : 'border-gray-300'}`}>
        <div className="max-w-7xl mx-auto text-center">
          <p className={darkMode ? 'text-gray-400' : 'text-gray-600'}>&copy; 2025 Axis Skynet. Built with Next.js and FastAPI. Open for everyone.</p>
        </div>
      </footer>
    </div>
  );
}
