import { useState, useEffect } from 'react'
import { Settings as SettingsIcon, Save, RefreshCw } from 'lucide-react'
import Card, { CardHeader, CardTitle, CardContent } from '../components/Card'
import Button from '../components/Button'
import { audioService } from '../services/audioService'
import { useAuthStore } from '../stores/authStore'
import toast from 'react-hot-toast'

export default function Settings() {
  const { user, updateProfile } = useAuthStore()
  const [health, setHealth] = useState(null)
  const [profile, setProfile] = useState({
    name: user?.name || '',
    email: user?.email || '',
  })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    checkSystemHealth()
  }, [])

  const checkSystemHealth = async () => {
    try {
      const data = await audioService.checkHealth()
      setHealth(data)
    } catch (error) {
      toast.error('Erro ao verificar saúde do sistema')
      console.error(error)
    }
  }

  const handleSaveProfile = () => {
    updateProfile(profile)
    toast.success('Perfil atualizado com sucesso!')
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Configurações</h1>
        <p className="text-gray-600 mt-1">Gerencie as configurações do sistema</p>
      </div>

      {/* Perfil do Usuário */}
      <Card>
        <CardHeader>
          <CardTitle>👤 Perfil do Usuário</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nome
            </label>
            <input
              type="text"
              value={profile.name}
              onChange={(e) => setProfile({ ...profile, name: e.target.value })}
              className="input"
              placeholder="Seu nome"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email
            </label>
            <input
              type="email"
              value={profile.email}
              onChange={(e) => setProfile({ ...profile, email: e.target.value })}
              className="input"
              placeholder="seu@email.com"
            />
          </div>

          <Button onClick={handleSaveProfile} icon={Save}>
            Salvar Alterações
          </Button>
        </CardContent>
      </Card>

      {/* Status do Sistema */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>🔧 Status do Sistema</CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={checkSystemHealth}
              icon={RefreshCw}
            >
              Atualizar
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {health ? (
            <>
              <ModelStatus
                name="Pyannote (Diarização)"
                loaded={health.models?.diarization?.loaded}
                device={health.models?.diarization?.device}
              />
              <ModelStatus
                name="Whisper (Transcrição Local)"
                loaded={health.models?.whisper?.loaded}
                device={health.models?.whisper?.device}
              />
              <ModelStatus
                name="AssemblyAI (Transcrição Cloud)"
                loaded={health.models?.assemblyai?.loaded}
                device={health.models?.assemblyai?.device}
              />
            </>
          ) : (
            <p className="text-gray-500">Carregando status...</p>
          )}
        </CardContent>
      </Card>

      {/* Informações do Sistema */}
      <Card>
        <CardHeader>
          <CardTitle>ℹ️ Informações do Sistema</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <InfoRow label="Versão" value="2.0.0" />
          <InfoRow label="API Backend" value="http://localhost:2020" />
          <InfoRow label="Status da API" value={health ? '🟢 Online' : '🔴 Offline'} />
          <InfoRow label="Banco de Dados" value={health?.database || 'N/A'} />
        </CardContent>
      </Card>
    </div>
  )
}

function ModelStatus({ name, loaded, device }) {
  return (
    <div className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
      <div>
        <p className="font-medium text-gray-900">{name}</p>
        <p className="text-sm text-gray-500">{device || 'Não carregado'}</p>
      </div>
      <span
        className={`badge ${loaded ? 'badge-success' : 'badge-error'}`}
      >
        {loaded ? 'Ativo' : 'Inativo'}
      </span>
    </div>
  )
}

function InfoRow({ label, value }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
      <span className="text-gray-600">{label}</span>
      <span className="font-medium text-gray-900">{value}</span>
    </div>
  )
}
