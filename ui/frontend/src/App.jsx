import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Datasets from './pages/Datasets'
import Training from './pages/Training'
import Loras from './pages/Loras'
import Generate from './pages/Generate'

const navItems = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/datasets', label: 'Datasets', icon: '📁' },
  { path: '/training', label: 'Training', icon: '🎯' },
  { path: '/loras', label: 'LoRAs', icon: '🧠' },
  { path: '/generate', label: 'Generate', icon: '🎨' }
]

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-900 text-white">
        <nav className="bg-gray-800 border-b border-gray-700 px-6 py-3">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2">
              <span className="text-2xl">☁️</span>
              <span className="font-bold text-xl bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                LoRA Cloud
              </span>
            </div>
            <div className="flex gap-1">
              {navItems.map(item => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
                      isActive
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`
                  }
                >
                  <span>{item.icon}</span>
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </div>
          </div>
        </nav>
        <main className="p-6 max-w-7xl mx-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/datasets" element={<Datasets />} />
            <Route path="/training" element={<Training />} />
            <Route path="/loras" element={<Loras />} />
            <Route path="/generate" element={<Generate />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
