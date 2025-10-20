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
    geminiApiKey: '',
  })
  const [showKeys, setShowKeys] = useState({
    hfToken: false,
    aaiApiKey: false,
    geminiApiKey: false,
  })
  const [loading, setLoading] = useState(false)
  const [savingKeys, setSavingKeys] = useState(false)

  useEffect(() => {
    checkSystemHealth()
    loadApiKeysStatus()
  }, [])

  const loadApiKeysStatus = async () => {
    try {
      await audioService.getApiKeysStatus()
      // Status carregado
    } catch (error) {
      console.error('Erro ao carregar status das API Keys:', error)
    }
  }

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
      
      // Validar se pelo menos uma chave foi preenchida
      if (!apiKeys.hfToken && !apiKeys.aaiApiKey && !apiKeys.geminiApiKey) {
        toast.error('Preencha pelo menos uma chave de API')
        return
      }
      
      // Enviar para o backend
      const result = await audioService.updateApiKeys(apiKeys)
      
      if (result.success) {
        toast.success('🎉 Chaves atualizadas e modelos recarregados!', {
          duration: 5000,
        })
        
        // Mostrar modelos atualizados
        if (result.updated_models && result.updated_models.length > 0) {
          const modelsMsg = result.updated_models
            .map(m => `✅ ${m.model}: ${m.device}`)
            .join('\n')
          
          toast.success(modelsMsg, {
            duration: 6000,
            style: {
              whiteSpace: 'pre-line',
            }
          })
        }
        
        // Atualizar status do sistema
        await checkSystemHealth()
        
        // Manter as chaves nos campos para referência
        // setApiKeys({ hfToken: '', aaiApiKey: '' })
      } else {
        // Mostrar erros detalhados
        if (result.errors && result.errors.length > 0) {
          result.errors.forEach(error => {
            if (error.includes('Token inválido') || error.includes('401')) {
              toast.error(
                <div className="space-y-2">
                  <p className="font-semibold">❌ {error}</p>
                  <p className="text-xs">
                    Verifique se:
                    <br />• O token está correto (começa com hf_)
                    <br />• Tem permissão "Read"
                    <br />• Foi criado em: huggingface.co/settings/tokens
                  </p>
                </div>,
                { duration: 10000 }
              )
            } else if (error.includes('Acesso negado') || error.includes('403')) {
              toast.error(
                <div className="space-y-2">
                  <p className="font-semibold">❌ {error}</p>
                  <p className="text-xs">
                    Aceite os termos de uso:
                    <br />• https://huggingface.co/pyannote/speaker-diarization
                    <br />• https://huggingface.co/pyannote/segmentation
                  </p>
                </div>,
                { duration: 10000 }
              )
            } else {
              toast.error(error, { duration: 8000 })
            }
          })
        }
        
        // Se algum modelo foi carregado com sucesso, mostrar
        if (result.updated_models && result.updated_models.length > 0) {
          const modelsMsg = result.updated_models
            .map(m => `✅ ${m.model}: ${m.device}`)
            .join('\n')
          
          toast.success('Modelos carregados parcialmente:\n' + modelsMsg, {
            duration: 6000,
            style: {
              whiteSpace: 'pre-line',
            }
          })
        }
        
        // Atualizar status do sistema mesmo com erros
        await checkSystemHealth()
      }
      
    } catch (error) {
      console.error(error)
      toast.error('Erro ao salvar chaves de API: ' + (error.response?.data?.detail || error.message))
    } finally {
      setSavingKeys(false)
    }
  }

  const toggleKeyVisibility = (key) => {
    setShowKeys(prev => ({ ...prev, [key]: !prev[key] }))
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
              <ModelStatus
                name="Gemini (Geração de Atas)"
                loaded={health.models?.gemini?.loaded}
                device={health.models?.gemini?.device}
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
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <p className="text-sm text-blue-800">
              <strong>💡 Como funciona:</strong> Digite suas chaves abaixo e clique em "Salvar e Ativar". Os modelos serão recarregados automaticamente sem necessidade de reiniciar o servidor!
            </p>
          </div>

          {/* Alertas de Requisitos */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 space-y-2">
            <h4 className="text-sm font-semibold text-yellow-900">⚠️ Requisitos do Hugging Face Token:</h4>
            <ul className="text-xs text-yellow-800 space-y-1 list-disc list-inside ml-2">
              <li>Token deve ter permissão <strong>"Read"</strong></li>
              <li>Token deve começar com <code className="bg-yellow-100 px-1 rounded">hf_</code></li>
              <li>Para Pyannote, aceite os termos em:
                <ul className="ml-4 mt-1 space-y-1">
                  <li>→ <a href="https://huggingface.co/pyannote/speaker-diarization" target="_blank" rel="noopener noreferrer" className="text-yellow-900 underline hover:text-yellow-700">speaker-diarization</a></li>
                  <li>→ <a href="https://huggingface.co/pyannote/segmentation" target="_blank" rel="noopener noreferrer" className="text-yellow-900 underline hover:text-yellow-700">segmentation</a></li>
                </ul>
              </li>
            </ul>
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

          {/* Gemini API Key */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ✨ Google Gemini API Key
              <span className="text-xs text-gray-500 ml-2">(Para geração de atas de reunião)</span>
            </label>
            <div className="relative">
              <input
                type={showKeys.geminiApiKey ? 'text' : 'password'}
                value={apiKeys.geminiApiKey}
                onChange={(e) => setApiKeys({ ...apiKeys, geminiApiKey: e.target.value })}
                className="input pr-10"
                placeholder="AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
              />
              <button
                type="button"
                onClick={() => toggleKeyVisibility('geminiApiKey')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showKeys.geminiApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Obtenha em: <a href="https://makersuite.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">https://makersuite.google.com/app/apikey</a>
            </p>
          </div>

          {/* Instruções */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-green-900 mb-2">✨ Funcionalidade Automática:</h4>
            <ul className="text-sm text-green-800 space-y-1 list-disc list-inside">
              <li>Digite suas chaves nos campos acima</li>
              <li>Clique em "Salvar e Ativar"</li>
              <li>Os modelos serão carregados automaticamente</li>
              <li>Sem necessidade de reiniciar o servidor! 🎉</li>
            </ul>
          </div>

          <Button
            onClick={handleSaveApiKeys}
            loading={savingKeys}
            disabled={!apiKeys.hfToken && !apiKeys.aaiApiKey && !apiKeys.geminiApiKey}
            icon={Save}
            className="w-full"
          >
            {savingKeys ? 'Salvando e Recarregando...' : 'Salvar e Ativar Modelos'}
          </Button>
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
            label="Google Gemini - Obter API Key"
            url="https://makersuite.google.com/app/apikey"
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
