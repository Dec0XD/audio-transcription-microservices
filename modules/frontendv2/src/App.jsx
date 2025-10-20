import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Transcriptions from './pages/Transcriptions'
import TranscriptionDetail from './pages/TranscriptionDetail'
import NewTranscription from './pages/NewTranscription'
import Settings from './pages/Settings'
import { useAuthStore } from './stores/authStore'

function App() {
  const { user } = useAuthStore()

  return (
    <Router>
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          error: {
            duration: 5000,
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
      
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="transcriptions" element={<Transcriptions />} />
          <Route path="transcriptions/:id" element={<TranscriptionDetail />} />
          <Route path="new-transcription" element={<NewTranscription />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default App
