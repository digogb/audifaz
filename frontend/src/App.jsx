import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { ConcursoProvider } from './contexts/ConcursoContext'
import { ThemeProvider } from './contexts/ThemeProvider'
import Layout from './components/Layout'
import Login from './pages/Login'
import Today from './pages/Today'
import Errors from './pages/Errors'
import Progress from './pages/Progress'
import Mocks from './pages/Mocks'
import Config from './pages/Config'
import Metricas from './pages/Metricas'
import Redacao from './pages/Redacao'

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<ProtectedRoute><Layout><Today /></Layout></ProtectedRoute>} />
      <Route path="/erros" element={<ProtectedRoute><Layout><Errors /></Layout></ProtectedRoute>} />
      <Route path="/progresso" element={<ProtectedRoute><Layout><Progress /></Layout></ProtectedRoute>} />
      <Route path="/simulados" element={<ProtectedRoute><Layout><Mocks /></Layout></ProtectedRoute>} />
      <Route path="/metricas" element={<ProtectedRoute><Layout><Metricas /></Layout></ProtectedRoute>} />
      <Route path="/redacao" element={<ProtectedRoute><Layout><Redacao /></Layout></ProtectedRoute>} />
      <Route path="/config" element={<ProtectedRoute><Layout><Config /></Layout></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ConcursoProvider>
          <ThemeProvider>
            <AppRoutes />
          </ThemeProvider>
        </ConcursoProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
