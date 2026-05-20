import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { BrandProvider } from './contexts/BrandContext'
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
import Plano from './pages/Plano'
import Redacao from './pages/Redacao'
import Signup from './pages/Signup'
import Landing from './pages/Landing'
import Billing from './pages/Billing'
import Termos from './pages/Termos'
import Privacidade from './pages/Privacidade'

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/landing" element={<Landing />} />
      <Route path="/termos" element={<Termos />} />
      <Route path="/privacidade" element={<Privacidade />} />
      <Route path="/billing" element={<ProtectedRoute><Layout><Billing /></Layout></ProtectedRoute>} />
      <Route path="/" element={<ProtectedRoute><Layout><Today /></Layout></ProtectedRoute>} />
      <Route path="/erros" element={<ProtectedRoute><Layout><Errors /></Layout></ProtectedRoute>} />
      <Route path="/progresso" element={<ProtectedRoute><Layout><Progress /></Layout></ProtectedRoute>} />
      <Route path="/simulados" element={<ProtectedRoute><Layout><Mocks /></Layout></ProtectedRoute>} />
      <Route path="/metricas" element={<ProtectedRoute><Layout><Metricas /></Layout></ProtectedRoute>} />
      <Route path="/plano" element={<ProtectedRoute><Layout><Plano /></Layout></ProtectedRoute>} />
      <Route path="/redacao" element={<ProtectedRoute><Layout><Redacao /></Layout></ProtectedRoute>} />
      <Route path="/config" element={<ProtectedRoute><Layout><Config /></Layout></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <BrandProvider>
        <AuthProvider>
          <ConcursoProvider>
            <ThemeProvider>
              <AppRoutes />
            </ThemeProvider>
          </ConcursoProvider>
        </AuthProvider>
      </BrandProvider>
    </BrowserRouter>
  )
}
