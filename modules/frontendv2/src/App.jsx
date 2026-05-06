import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Transcriptions from './pages/Transcriptions'
import TranscriptionDetail from './pages/TranscriptionDetail'
import NewTranscription from './pages/NewTranscription'
import MeetingMinutes from './pages/MeetingMinutes'
import Settings from './pages/Settings'
import Login from './pages/Login'
import { authService } from './services/authService'
import { useAuthStore } from './stores/authStore'

function App() {
  const {
    isAuthenticated,
    authMode,
    setAuthMode,
    setSession,
    enableDemoSession,
  } = useAuthStore()
  const [bootstrapped, setBootstrapped] = useState(false)

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const config = await authService.getConfig()
        setAuthMode(config.mode)

        const token = localStorage.getItem('token')
        if (token) {
          const me = await authService.me()
          if (me.authenticated) {
            setSession(me.user, token)
            setBootstrapped(true)
            return
          }
        }

        if (config.mode === 'permissive') {
          enableDemoSession()
        }
      } catch {
        // Se backend indisponível, mantém experiência anterior em modo demo.
        enableDemoSession()
      } finally {
        setBootstrapped(true)
      }
    }

    bootstrap()
  }, [setAuthMode, setSession, enableDemoSession])

  if (!bootstrapped) {
    return null
  }

  const requiresLogin = authMode === 'strict' && !isAuthenticated

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
        <Route path="/login" element={<Login />} />

        {requiresLogin ? (
          <Route path="*" element={<Navigate to="/login" replace />} />
        ) : (
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="transcriptions" element={<Transcriptions />} />
          <Route path="transcriptions/:id" element={<TranscriptionDetail />} />
          <Route path="new-transcription" element={<NewTranscription />} />
          <Route path="meeting-minutes" element={<MeetingMinutes />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
        )}
      </Routes>
    </Router>
  )
}

export default App
