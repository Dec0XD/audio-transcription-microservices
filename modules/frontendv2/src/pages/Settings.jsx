import { useState, useEffect } from 'react'
import { Settings as SettingsIcon, Save, RefreshCw, Key, Eye, EyeOff } from 'lucide-react'
import Card, { CardHeader, CardTitle, CardContent } from '../components/Card'
import Button from '../components/Button'
import ApiKeyGuide from '../components/ApiKeyGuide'
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
  const [apiKeys, setApiKeys] = useState({
    hfToken: '',
    aaiApiKey: '',
  })
  const [showKeys, setShowKeys] = useState({
    hfToken: false,
    aaiApiKey: false,
  })
  const [loading, setLoading] = useState(false)
  const [savingKeys, setSavingKeys] = useState(false)

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

  const handleSaveApiKeys = async () => {
    try {
      setSavingKeys(true)
      
      // Salvar no localStorage (em produção, isso deveria ir para o backend)
      if (apiKeys.hfToken) {
        localStorage.setItem('HF_TOKEN', apiKeys.hfToken)
      }
      if (apiKeys.aaiApiKey) {
        localStorage.setItem('AAI_API_KEY', apiKeys.aaiApiKey)
      }
      
      toast.success('Chaves de API salvas! Reinicie o backend para aplicar as mudanças.')
      
      // Mostrar instruções
      toast('Para aplicar: Adicione as chaves no arquivo .env do backend e reinicie', {
        duration: 8000,
        icon: 'ℹ️',
      })
    } catch (error) {
      toast.error('Erro ao salvar chaves de API')
    } finally {
      setSavingKeys(false)
    }
  }

  const toggleKeyVisibility = (key) => {
    setShowKeys(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const copyEnvTemplate = () => {
    const envContent = `# API Keys
HF_TOKEN=${apiKeys.hfToken || 'sua_chave_huggingface_aqui'}
AAI_API_KEY=${apiKeys.aaiApiKey || 'sua_chave_assemblyai_aqui'}

# Database Configuration
DATABASE_URL=sqlite:///./database/transcriptions.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=2020
DEBUG=True

# File Upload Configuration
MAX_UPLOAD_SIZE_MB=500
ALLOWED_EXTENSIONS=mp3,wav,mp4,mpeg,m4a,flac,ogg,opus

# Processing Configuration
DEFAULT_TRANSCRIPTION_MODEL=whisper
MIN_SEGMENT_DURATION=0.7
SILENCE_THRESHOLD=-30`

    navigator.clipboard.writeText(envContent)
    toast.success('Conteúdo do .env copiado! Cole no arquivo modules/backend/.env')
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

      {/* Configuração de API Keys */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>🔑 Chaves de API</CardTitle>
            <ApiKeyGuide />
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
            <p className="text-sm text-yellow-800">
              <strong>⚠️ Importante:</strong> As chaves de API devem ser configuradas no arquivo <code className="bg-yellow-100 px-1 rounded">.env</code> do backend e o servidor deve ser reiniciado.
            </p>
          </div>

          {/* Hugging Face Token */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              🤗 Hugging Face Token
              <span className="text-xs text-gray-500 ml-2">(Para Whisper e Pyannote)</span>
            </label>
            <div className="relative">
              <input
                type={showKeys.hfToken ? 'text' : 'password'}
                value={apiKeys.hfToken}
                onChange={(e) => setApiKeys({ ...apiKeys, hfToken: e.target.value })}
                className="input pr-10"
                placeholder="hf_xxxxxxxxxxxxxxxxxxxxx"
              />
              <button
                type="button"
                onClick={() => toggleKeyVisibility('hfToken')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showKeys.hfToken ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Obtenha em: <a href="https://huggingface.co/settings/tokens" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">https://huggingface.co/settings/tokens</a>
            </p>
          </div>

          {/* AssemblyAI API Key */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ☁️ AssemblyAI API Key
              <span className="text-xs text-gray-500 ml-2">(Para transcrição cloud)</span>
            </label>
            <div className="relative">
              <input
                type={showKeys.aaiApiKey ? 'text' : 'password'}
                value={apiKeys.aaiApiKey}
                onChange={(e) => setApiKeys({ ...apiKeys, aaiApiKey: e.target.value })}
                className="input pr-10"
                placeholder="xxxxxxxxxxxxxxxxxxxxxxxx"
              />
              <button
                type="button"
                onClick={() => toggleKeyVisibility('aaiApiKey')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showKeys.aaiApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Obtenha em: <a href="https://www.assemblyai.com/dashboard/signup" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">https://www.assemblyai.com/dashboard</a>
            </p>
          </div>

          {/* Instruções */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-blue-900 mb-2">📝 Como Configurar:</h4>
            <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
              <li>Preencha as chaves acima</li>
              <li>Clique em "Copiar Configuração .env"</li>
              <li>Cole o conteúdo no arquivo <code className="bg-blue-100 px-1 rounded">modules/backend/.env</code></li>
              <li>Reinicie o servidor backend</li>
              <li>Atualize esta página para ver os modelos ativos</li>
            </ol>
          </div>

          <div className="flex gap-2">
            <Button
              onClick={copyEnvTemplate}
              variant="outline"
              icon={Key}
            >
              Copiar Configuração .env
            </Button>
            <Button
              onClick={handleSaveApiKeys}
              loading={savingKeys}
              icon={Save}
            >
              Salvar Localmente
            </Button>
          </div>
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

      {/* Links Úteis */}
      <Card>
        <CardHeader>
          <CardTitle>🔗 Links Úteis</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <LinkRow
            label="Hugging Face - Criar Token"
            url="https://huggingface.co/settings/tokens"
          />
          <LinkRow
            label="AssemblyAI - Criar Conta"
            url="https://www.assemblyai.com/dashboard/signup"
          />
          <LinkRow
            label="Pyannote - Aceitar Termos de Uso"
            url="https://huggingface.co/pyannote/speaker-diarization"
          />
          <LinkRow
            label="Documentação do Projeto"
            url="https://github.com/Dec0XD/audio-transcription-microservices"
          />
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

function LinkRow({ label, url }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
      <span className="text-gray-600">{label}</span>
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-primary-600 hover:text-primary-700 text-sm font-medium hover:underline"
      >
        Acessar →
      </a>
    </div>
  )
}
