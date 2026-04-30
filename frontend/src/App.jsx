import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Today from './pages/Today'
import Errors from './pages/Errors'
import Progress from './pages/Progress'
import Mocks from './pages/Mocks'

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Today />} />
          <Route path="/erros" element={<Errors />} />
          <Route path="/progresso" element={<Progress />} />
          <Route path="/simulados" element={<Mocks />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
