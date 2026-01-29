import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Datasets from './pages/Datasets'
import Training from './pages/Training'
import Loras from './pages/Loras'
import Generate from './pages/Generate'

const navItems = [
  { path: '/', label: 'Dashboard' },
  { path: '/datasets', label: 'Datasets' },
  { path: '/training', label: 'Training' },
  { path: '/loras', label: 'LoRAs' },
  { path: '/generate', label: 'Generate' }
]

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-900 text-white">
        <nav className="bg-gray-800 px-6 py-4">
          <div className="flex gap-6">
            <span className="font-bold text-xl">LoRA Cloud</span>
            {navItems.map(item => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `px-3 py-1 rounded ${isActive ? 'bg-blue-600' : 'hover:bg-gray-700'}`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </div>
        </nav>
        <main className="p-6">
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
