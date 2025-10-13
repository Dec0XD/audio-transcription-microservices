<a name="readme-top"></a>

<!-- PROJECT SHIELDS -->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/Dec0XD/audio-transcription-microservices">
    <img src="imgs/Inicial.png" alt="Logo" width="1000" height="500">
  </a>
  <h3 align="center">Transcrição de Áudio/Vídeo com Segmentação de Falantes</h3>
  <p align="center">
    Uma aplicação de transcrição de áudio/vídeo com segmentação de falantes, usando uma arquitetura de microserviços com Streamlit, FastAPI, Whisper, AssemblyAI e Pyannote, otimizada para execução local com suporte a GPU.
    <br />
    <a href="https://github.com/Dec0XD/audio-transcription-microservices"><strong>Explore a documentação »</strong></a>
    <br />
    <br />
    <a href="https://github.com/Dec0XD/audio-transcription-microservices">Ver Demonstração</a>
    ·
    <a href="https://github.com/Dec0XD/audio-transcription-microservices/issues">Reportar Bug</a>
    ·
    <a href="https://github.com/Dec0XD/audio-transcription-microservices/issues">Solicitar Funcionalidade</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Índice</summary>
  <ol>
    <li>
      <a href="#sobre-o-projeto">Sobre o Projeto</a>
      <ul>
        <li><a href="#construído-com">Construído Com</a></li>
      </ul>
    </li>
    <li>
      <a href="#primeiros-passos">Primeiros Passos</a>
      <ul>
        <li><a href="#pré-requisitos">Pré-requisitos</a></li>
        <li><a href="#instalação">Instalação</a></li>
      </ul>
    </li>
    <li><a href="#uso">Uso</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contribuição">Contribuição</a></li>
    <li><a href="#licença">Licença</a></li>
    <li><a href="#contato">Contato</a></li>
    <li><a href="#agradecimentos">Agradecimentos</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## Sobre o Projeto

Esta aplicação permite aos usuários fazer upload de arquivos de áudio ou vídeo, convertê-los para o formato .wav, transcrevê-los usando o modelo Whisper da OpenAI ou AssemblyAI, e, opcionalmente, segmentar os falantes com o Pyannote. **Totalmente reformulada com arquitetura integrada**, o sistema agora executa todos os serviços em um único processo FastAPI otimizado, utilizando Streamlit para uma interface de usuário intuitiva. O projeto é **altamente otimizado para GPUs NVIDIA** (RTX 3060, RTX 4090, etc.), aproveitando CUDA e half-precision para acelerar significativamente o processamento de Whisper e Pyannote.

### 🚀 Nova Arquitetura Integrada

O projeto foi **completamente reestruturado** para máxima simplicidade e performance:

```
📁 Transcricao-de-audio/
├── 📁 modules/backend/
│   ├── 📁 src/
│   │   ├── main.py                    # API Gateway Integrado (Porta 2020)
│   │   ├── config.py                  # Configurações (.env, GPU settings)
│   │   ├── models.py                  # Modelos SQLAlchemy
│   │   ├── security.py                # Autenticação JWT
│   │   ├── 📁 services/
│   │   │   ├── diarization_engine.py  # Pyannote GPU-optimized
│   │   │   ├── transcription_engine.py # Whisper + AssemblyAI engines
│   │   │   ├── diarization.py         # Legacy service
│   │   │   ├── transcription.py       # Legacy service
│   │   │   └── orchestrator.py        # Service orchestration
│   │   └── 📁 utils/
│   │       └── gpu_utils.py           # Otimizações CUDA/cuDNN
│   ├── requirements.txt               # Dependências Python
│   ├── .env.example                   # Template de configuração
│   └── 📁 database/                   # SQLite database
├── 📁 frontend/
│   └── app.py                         # Interface Streamlit
└── .env                               # Configurações principais
```

**✨ Principais Melhorias:**
- **Processo Único** - Um comando inicia tudo (porta 2020)
- **GPU First** - Detecção automática e otimização CUDA
- **Performance** - Whisper Large em GPU ~10x mais rápido
- **Configuração Simples** - Scripts PowerShell automatizados
- **Memória Otimizada** - Half-precision (float16) para RTX series
- **Health Checks** - Monitoramento de modelos em tempo real
- **Logs Detalhados** - Informações de GPU, VRAM e tempos

### Principais Recursos

- **Transcrição Automática**: Suporte a Whisper (local) e AssemblyAI (cloud) com seleção de modelo.
- **Segmentação de Falantes**: Identifica quem fala e quando, usando Pyannote, com filtragem de segmentos curtos ou silenciosos para maior robustez.
- **Interface Intuitiva**: Streamlit oferece uma UI simples com verificação de disponibilidade dos modelos.
- **Otimização para CPU/GPU**: Funciona em CPUs com tempos de processamento ajustados ou GPUs para maior rapidez.
- **Progresso no Terminal**: Exibe progresso da diarização no terminal.

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

### Construído Com
- **Python 3.11+** - Runtime principal
- **Streamlit** - Interface web interativa
- **FastAPI** - API REST backend
- **PyTorch + CUDA** - Framework de ML com aceleração GPU
- **Transformers (Hugging Face)** - Whisper Large v3
- **Pyannote.audio** - Diarização de falantes
- **AssemblyAI** - Transcrição cloud (alternativa)
- **SQLAlchemy** - ORM para persistência
- **Pydantic** - Validação e configuração
- **librosa + pydub** - Processamento de áudio
- **NVIDIA CUDA + cuDNN** - Aceleração GPU

### 🏗️ Arquitetura Integrada

```
┌─────────────┐
│  Frontend   │ Streamlit (Port 8501)
└──────┬──────┘
       │ HTTP REST
       ▼
┌────────────────────────────────────────────┐
│         Backend Integrado                  │ FastAPI (Port 2020)
│  ┌──────────────────────────────────────┐  │
│  │  Engines Carregados na Startup      │  │
│  │  ┌────────────┐ ┌────────────────┐  │  │
│  │  │ Pyannote   │ │ Whisper Large  │  │  │
│  │  │ (GPU/CUDA) │ │ (GPU/float16)  │  │  │
│  │  └────────────┘ └────────────────┘  │  │
│  │  ┌────────────────────────────────┐  │  │
│  │  │     AssemblyAI Client          │  │  │
│  │  └────────────────────────────────┘  │  │
│  └──────────────────────────────────────┘  │
│  • Orquestração Integrada                 │
│  • Autenticação JWT                       │
│  • Persistência SQLite                    │
│  • Health Checks                          │
│  • GPU Optimization                       │
└────────────────────┬───────────────────────┘
                     │
                     ▼
            ┌────────────────┐
            │ NVIDIA GPU     │
            │ CUDA + cuDNN   │ 
            │ (RTX 3060+)    │
            └────────────────┘
```

**Fluxo Otimizado:**
1. **Startup**: Modelos carregados uma vez na GPU
2. **Upload**: Frontend → Backend unificado
3. **Processamento**: Engines internos (sem HTTP overhead)
4. **Diarização**: Pyannote identifica falantes na GPU
5. **Transcrição**: Whisper processa segmentos em float16
6. **Resposta**: Resultados agregados e persistidos

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

<!-- GETTING STARTED -->
## Primeiros Passos

### Pré-requisitos
- **Python 3.11+** (recomendado para melhor compatibilidade)
- **Conta no Hugging Face** (token necessário para Pyannote)
- **Conta na AssemblyAI** (opcional, para transcrição cloud)
- **FFmpeg** (conversão de áudio/vídeo)
- **GPU NVIDIA** (recomendado):
  - CUDA Toolkit 11.8 ou 12.x
  - cuDNN 8.9+
  - Driver NVIDIA 531+ (para RTX series)
  - **VRAM mínima**: 8GB

### Instalação

#### 🚀 Instalação Rápida (Recomendado)

**1. Clone e Configure:**
```powershell
git clone https://github.com/Dec0XD/audio-transcription-microservices.git
cd audio-transcription-microservices
```

**2. Configure o Ambiente:**
```powershell
cd modules\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Para GPU NVIDIA (recomendado)
pip uninstall -y torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**3. Configurar API Keys:**
```powershell
# Copie e edite o arquivo .env na raiz do projeto
copy modules\backend\.env.example .env
# OU edite o .env existente na raiz
```

**.env (obrigatório - localizado na raiz do projeto):**
```ini
# Hugging Face (obrigatório para Pyannote)
HF_TOKEN=seu_token_huggingface_aqui

# AssemblyAI (opcional, para transcrição cloud)
AAI_API_KEY=seu_token_assemblyai_aqui

# Configurações de GPU (opcional)
FORCE_CPU=false
GPU_MEMORY_FRACTION=0.8
WHISPER_DTYPE=auto
```

**4. Executar (2 comandos apenas!):**

Terminal 1 - Backend:
```powershell
cd modules\backend
python -m uvicorn src.main:app --host 0.0.0.0 --port 2020
```

Terminal 2 - Frontend:
```powershell
cd frontend
streamlit run app.py
```

**🔗 URLs:**
- **Frontend**: http://localhost:8501
- **API Docs**: http://localhost:2020/docs
- **Health Check**: http://localhost:2020/health

#### 🛠️ Comandos Úteis

Verificar se os modelos estão funcionando:

```powershell
# Testar PyTorch + CUDA
python -c "import torch; print(f'CUDA disponível: {torch.cuda.is_available()}')"

# Verificar dependências essenciais
python -c "import transformers, pyannote.audio, librosa; print('Todas as dependências OK')"
```

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

<!-- USAGE EXAMPLES -->
## Uso

### Interface Web (Streamlit)

1. **Acesse** http://localhost:8501
2. **Verifique** o status dos modelos no sidebar:
   - ✅ Pyannote (GPU) - Diarização
   - ✅ Whisper Large (GPU) - Transcrição local  
   - ✅ AssemblyAI - Transcrição cloud
3. **Upload** de arquivos de áudio/vídeo (MP3, WAV, MP4, etc.)
4. **Configure** opções de processamento
5. **Monitore** progresso em tempo real

### Exemplos de Resultado

**Com Diarização (GPU ~30s para 2min de áudio):**
```
🎯 Arquivo: reuniao.mp3 (2.5 MB, 2:15min)
⚡ Processamento: 28.3s total

📊 Falantes detectados: 3
🎤 SPEAKER_00 (0.0s - 15.2s): Bom dia pessoal, vamos começar nossa reunião de hoje...
🎤 SPEAKER_01 (15.5s - 45.8s): Perfeito, tenho alguns pontos importantes para discutir...
🎤 SPEAKER_02 (46.2s - 2:15.0s): Concordo completamente com essa abordagem...
```

**Sem Diarização (GPU ~15s):**
```
📝 Transcrição completa:
Bom dia pessoal, vamos começar nossa reunião de hoje. Perfeito, tenho alguns pontos importantes para discutir. Concordo completamente com essa abordagem...
```

### Performance Esperada

| Configuração | Whisper Large | Pyannote | Arquivo 2min |
|-------------|---------------|----------|--------------|
| **RTX 3060** | ~8s | ~15s | **~25s total** |
| **RTX 4090** | ~4s | ~8s | **~15s total** |
| **CPU apenas** | ~120s | ~300s | **~7min total** |

### API REST (Opcional)

```bash
# Health check
curl http://localhost:2020/health

# Upload e transcrição
curl -X POST "http://localhost:2020/transcribe" \
  -F "file=@audio.mp3" \
  -F "enable_diarization=true"
```

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

<!-- ROADMAP -->
## Roadmap

### Concluído ✅
- [x] **Arquitetura integrada** - Processo único na porta 2020
- [x] **Otimização GPU completa** - CUDA, cuDNN, half-precision
- [x] **Whisper Large GPU** - ~10x mais rápido que CPU
- [x] **Pyannote GPU** - Diarização acelerada
- [x] **Interface Streamlit** - Health checks e progresso
- [x] **Scripts automatizados** - PowerShell para Windows
- [x] **API REST FastAPI** - Endpoints documentados
- [x] **Persistência SQLite** - Histórico de transcrições
- [x] **Configuração .env** - GPU settings, API keys
- [x] **Logging detalhado** - VRAM, timings, device info

### Em Progresso 🔄
- [ ] **Testes automatizados** - Cobertura completa
- [ ] **Docker simplificado** - Single container
- [ ] **Rate limiting** - Proteção da API

### Planejado 📋
- [ ] **Multi-GPU support** - Distribuição de carga
- [ ] **Quantização INT8** - Menor uso de VRAM
- [ ] **Streaming transcription** - Tempo real
- [ ] **Whisper fine-tuning** - Português brasileiro
- [ ] **Web interface** - React/Vue alternativa
- [ ] **Batch processing** - Múltiplos arquivos
- [ ] **Export formats** - SRT, VTT, JSON
- [ ] **Real-time diarization** - Microfone ao vivo
- [ ] **Cloud deployment** - AWS/GCP/Azure guides

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

<!-- CONTRIBUTING -->
## Contribuição

1. Fork do repositório
2. `git checkout -b feature/NovaFuncionalidade`
3. `git commit -m 'Adiciona NovaFuncionalidade'`
4. `git push origin feature/NovaFuncionalidade`
5. Abra um Pull Request

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

<!-- LICENSE -->
## Licença

Distribuído sob a licença MIT. Veja `LICENSE.txt` para mais informações.

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

<!-- CONTACT -->
## Contato

André Coêlho - [Instagram](https://www.instagram.com/coelhoandrelucas/) - andrecoedev@gmail.com  
Projeto: [https://github.com/Dec0XD/audio-transcription-microservices](https://github.com/Dec0XD/audio-transcription-microservices)

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

<!-- ACKNOWLEDGMENTS -->
## Agradecimentos

- Streamlit
- FastAPI
- Whisper
- AssemblyAI
- Pyannote
- PyTorch
- NVIDIA CUDA
- FFmpeg

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
[contributors-shield]: https://img.shields.io/github/contributors/Dec0XD/audio-transcription-microservices.svg?style=for-the-badge
[contributors-url]: https://github.com/Dec0XD/audio-transcription-microservices/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/Dec0XD/audio-transcription-microservices.svg?style=for-the-badge
[forks-url]: https://github.com/Dec0XD/audio-transcription-microservices/network/members
[stars-shield]: https://img.shields.io/github/stars/Dec0XD/audio-transcription-microservices.svg?style=for-the-badge
[stars-url]: https://github.com/Dec0XD/audio-transcription-microservices/stargazers
[issues-shield]: https://img.shields.io/github/issues/Dec0XD/audio-transcription-microservices.svg?style=for-the-badge
[issues-url]: https://github.com/Dec0XD/audio-transcription-microservices/issues
[license-shield]: https://img.shields.io/github/license/Dec0XD/audio-transcription-microservices.svg?style=for-the-badge
[license-url]: https://github.com/Dec0XD/audio-transcription-microservices/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/andré-coêlho-b55b0622a/
