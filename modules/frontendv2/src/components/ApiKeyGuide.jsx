import { useState } from 'react'
import Modal from '../components/Modal'
import Button from '../components/Button'
import { HelpCircle } from 'lucide-react'

export default function ApiKeyGuide() {
  const [isOpen, setIsOpen] = useState(false)
  const [activeTab, setActiveTab] = useState('huggingface')

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(true)}
        icon={HelpCircle}
      >
        Como Obter as Chaves
      </Button>

      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="🔑 Guia de Configuração de API Keys"
      >
        <div className="space-y-6">
          {/* Tabs */}
          <div className="flex gap-2 border-b border-gray-200">
            <button
              onClick={() => setActiveTab('huggingface')}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'huggingface'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              🤗 Hugging Face
            </button>
            <button
              onClick={() => setActiveTab('assemblyai')}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'assemblyai'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              ☁️ AssemblyAI
            </button>
            <button
              onClick={() => setActiveTab('pyannote')}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'pyannote'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              🎯 Pyannote
            </button>
          </div>

          {/* Content */}
          {activeTab === 'huggingface' && <HuggingFaceGuide />}
          {activeTab === 'assemblyai' && <AssemblyAIGuide />}
          {activeTab === 'pyannote' && <PyannoteGuide />}
        </div>
      </Modal>
    </>
  )
}

function HuggingFaceGuide() {
  return (
    <div className="space-y-4">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2">🤗 Hugging Face Token</h4>
        <p className="text-sm text-blue-800">
          Necessário para usar o Whisper (transcrição local) e Pyannote (diarização).
        </p>
      </div>

      <div className="space-y-3">
        <h5 className="font-semibold text-gray-900">Passo a Passo:</h5>
        
        <div className="space-y-2">
          <Step number="1" title="Criar Conta">
            <p>Acesse <a href="https://huggingface.co/join" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">https://huggingface.co/join</a> e crie uma conta gratuita.</p>
          </Step>

          <Step number="2" title="Acessar Configurações">
            <p>Após fazer login, vá para <a href="https://huggingface.co/settings/tokens" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">Settings → Access Tokens</a></p>
          </Step>

          <Step number="3" title="Criar Novo Token">
            <p>Clique em <strong>"New token"</strong> e escolha:</p>
            <ul className="list-disc list-inside ml-4 text-sm space-y-1 mt-2">
              <li>Nome: "Transcritor AI"</li>
              <li>Tipo: <strong>Read</strong></li>
            </ul>
          </Step>

          <Step number="4" title="Copiar Token">
            <p>Copie o token gerado (começa com <code className="bg-gray-100 px-1 rounded">hf_</code>) e cole nas configurações.</p>
          </Step>
        </div>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
        <p className="text-sm text-yellow-800">
          <strong>⚠️ Importante:</strong> O token é mostrado apenas uma vez. Guarde-o em local seguro!
        </p>
      </div>
    </div>
  )
}

function AssemblyAIGuide() {
  return (
    <div className="space-y-4">
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <h4 className="font-semibold text-green-900 mb-2">☁️ AssemblyAI API Key</h4>
        <p className="text-sm text-green-800">
          Necessário para transcrição cloud de alta qualidade. Oferece 5 horas gratuitas por mês.
        </p>
      </div>

      <div className="space-y-3">
        <h5 className="font-semibold text-gray-900">Passo a Passo:</h5>
        
        <div className="space-y-2">
          <Step number="1" title="Criar Conta">
            <p>Acesse <a href="https://www.assemblyai.com/dashboard/signup" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">https://www.assemblyai.com/dashboard/signup</a> e crie uma conta gratuita.</p>
          </Step>

          <Step number="2" title="Verificar Email">
            <p>Confirme seu email através do link enviado para sua caixa de entrada.</p>
          </Step>

          <Step number="3" title="Acessar Dashboard">
            <p>Após fazer login, você será direcionado automaticamente para o dashboard.</p>
          </Step>

          <Step number="4" title="Copiar API Key">
            <p>No dashboard, você encontrará sua API Key na seção <strong>"Your API Key"</strong>. Clique em <strong>"Copy"</strong> e cole nas configurações.</p>
          </Step>
        </div>
      </div>

      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
        <p className="text-sm text-green-800">
          <strong>✅ Plano Gratuito:</strong> 5 horas de transcrição por mês, sem necessidade de cartão de crédito!
        </p>
      </div>
    </div>
  )
}

function PyannoteGuide() {
  return (
    <div className="space-y-4">
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
        <h4 className="font-semibold text-purple-900 mb-2">🎯 Pyannote (Diarização)</h4>
        <p className="text-sm text-purple-800">
          Usa o mesmo token do Hugging Face, mas requer aceitar os termos de uso do modelo.
        </p>
      </div>

      <div className="space-y-3">
        <h5 className="font-semibold text-gray-900">Passo a Passo:</h5>
        
        <div className="space-y-2">
          <Step number="1" title="Ter Token Hugging Face">
            <p>Certifique-se de já ter criado um token do Hugging Face (veja aba anterior).</p>
          </Step>

          <Step number="2" title="Aceitar Termos - Diarization">
            <p>Acesse <a href="https://huggingface.co/pyannote/speaker-diarization" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">pyannote/speaker-diarization</a> e clique em <strong>"Agree and access repository"</strong></p>
          </Step>

          <Step number="3" title="Aceitar Termos - Segmentation">
            <p>Acesse <a href="https://huggingface.co/pyannote/segmentation" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">pyannote/segmentation</a> e clique em <strong>"Agree and access repository"</strong></p>
          </Step>

          <Step number="4" title="Usar Token">
            <p>Use o mesmo token do Hugging Face. A diarização funcionará automaticamente após aceitar os termos.</p>
          </Step>
        </div>
      </div>

      <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
        <p className="text-sm text-purple-800">
          <strong>📝 Nota:</strong> Os termos devem ser aceitos apenas uma vez. Após isso, o modelo estará disponível para sempre.
        </p>
      </div>
    </div>
  )
}

function Step({ number, title, children }) {
  return (
    <div className="flex gap-3">
      <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-600 text-white flex items-center justify-center text-sm font-bold">
        {number}
      </div>
      <div className="flex-1">
        <h6 className="font-medium text-gray-900 mb-1">{title}</h6>
        <div className="text-sm text-gray-600">{children}</div>
      </div>
    </div>
  )
}
