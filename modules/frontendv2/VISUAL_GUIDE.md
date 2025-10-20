# 🎨 Guia Visual - Frontend v2

## 🖥️ Layout Principal

```
┌────────────────────────────────────────────────────────────────────┐
│  🎙️ Transcritor AI                              UD  Usuário Demo  │ ← Navbar
├──────────┬─────────────────────────────────────────────────────────┤
│          │                                                          │
│ 📱 Menu  │              📄 Conteúdo da Página                      │
│          │                                                          │
│ • Home   │  ┌─────────────────────────────────────┐               │
│ • Nova   │  │                                     │               │
│ • Lista  │  │        Card / Conteúdo              │               │
│ • Config │  │                                     │               │
│          │  └─────────────────────────────────────┘               │
│  ─────   │                                                          │
│ Status   │                                                          │
│ Modelos  │                                                          │
│ Falantes │                                                          │
│          │                                                          │
│ 💡 Dica  │                                                          │
│          │                                                          │
└──────────┴─────────────────────────────────────────────────────────┘
```

## 📊 Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│  Dashboard                                    [Nova Transcrição] │
│  Visão geral do sistema de transcrição                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  🧠 Status dos Modelos                                           │
│  ┌─────────────────┬─────────────────┬──────────────────┐      │
│  │ 🎯 Diarização   │ 🎙️ Whisper     │ ☁️ AssemblyAI    │      │
│  │ Pyannote        │ Local           │ Cloud            │      │
│  │ 🟢 cuda:0       │ 🟢 cuda:0       │ 🟢 Cloud         │      │
│  └─────────────────┴─────────────────┴──────────────────┘      │
│                                                                   │
│  ┌──────────┬──────────┬──────────┬──────────┐                 │
│  │ 📊 Total │ ✅ Concl │ ⏱️ Proc  │ ❌ Falh  │                 │
│  │    15    │    12    │     2    │     1    │                 │
│  └──────────┴──────────┴──────────┴──────────┘                 │
│                                                                   │
│  📋 Transcrições Recentes                      [Ver Todas]      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ 🎵 audio_reuniao.mp3        12/01 15:30  ✅ Concluída │    │
│  │ 🎵 entrevista_cliente.mp3   12/01 14:20  ✅ Concluída │    │
│  │ 🎵 podcast_ep1.mp3          12/01 13:10  ⏱️ Processando│   │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## 📤 Nova Transcrição

```
┌─────────────────────────────────────────────────────────────────┐
│  Nova Transcrição                                                │
│  Faça upload de um arquivo de áudio ou vídeo para transcrever  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📁 Upload de Arquivo                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                           │   │
│  │                    📥                                     │   │
│  │    Arraste um arquivo ou clique para selecionar         │   │
│  │                                                           │   │
│  │  Formatos: MP3, WAV, MP4, M4A, FLAC (máx. 100MB)       │   │
│  │                                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ⚙️ Configurações                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Modelo de Transcrição:                                   │   │
│  │  [🎙️ Whisper - Local]  [☁️ AssemblyAI - Cloud]        │   │
│  │                                                           │   │
│  │ 🗣️ Segmentação de Falantes              [ON/OFF]       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│                               [Cancelar] [Iniciar Transcrição]  │
└─────────────────────────────────────────────────────────────────┘
```

## 📋 Lista de Transcrições

```
┌─────────────────────────────────────────────────────────────────┐
│  Transcrições                               [Nova Transcrição]  │
│  Gerencie todas as suas transcrições                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  [🔍 Buscar...              ] [🔽 Status: Todos]                │
│                                                                   │
│  📋 Todas as Transcrições (15)                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ 🎵 audio_reuniao.mp3                                   │    │
│  │    📅 12/01/2025  ⏱️ 125.5s  📝 345 palavras         │    │
│  │                              ✅ Concluída [👁️][🗑️]    │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ 🎵 entrevista_cliente.mp3                              │    │
│  │    📅 12/01/2025  ⏱️ 450.2s  📝 1230 palavras        │    │
│  │                              ✅ Concluída [👁️][🗑️]    │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ 🎵 podcast_ep1.mp3                                     │    │
│  │    📅 12/01/2025  ⏱️ 2400.0s  📝 5000 palavras       │    │
│  │                             ⏱️ Processando [👁️][🗑️]   │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                   │
│                                            [1] [2] [3] ... [5]  │
└─────────────────────────────────────────────────────────────────┘
```

## 🔍 Detalhes da Transcrição

```
┌─────────────────────────────────────────────────────────────────┐
│  [← Voltar]  audio_reuniao.mp3                                  │
│  Criado em 12/01/2025 15:30                                     │
│                        [📋 Copiar] [📥 TXT] [📥 JSON] [📥 SRT] │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────┬─────────┬─────────┬─────────┐                     │
│  │ ⏱️ 125s │📝 345   │🗣️ 3     │🎙️ Whisper│                   │
│  │ Duração │Palavras │Falantes │ Modelo   │                     │
│  └─────────┴─────────┴─────────┴─────────┘                     │
│                                                                   │
│  📝 Transcrição Completa                                         │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ ① Falante 0              0.0s - 15.5s                  │    │
│  │ Boa tarde a todos, vamos iniciar a reunião de hoje... │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ ② Falante 1              15.6s - 32.8s                 │    │
│  │ Obrigado pela presença. Hoje vamos discutir...        │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ ① Falante 0              33.0s - 48.2s                 │    │
│  │ Perfeito. Gostaria de começar apresentando...         │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## ⚙️ Configurações

```
┌─────────────────────────────────────────────────────────────────┐
│  Configurações                                                   │
│  Gerencie as configurações do sistema                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  👤 Perfil do Usuário                                            │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Nome:  [Usuário Demo                              ]    │    │
│  │ Email: [demo@transcricao.ai                       ]    │    │
│  │                                        [💾 Salvar]     │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                   │
│  🔧 Status do Sistema                          [🔄 Atualizar]   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Pyannote (Diarização)                      ✅ Ativo    │    │
│  │ cuda:0                                                  │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ Whisper (Transcrição Local)               ✅ Ativo    │    │
│  │ cuda:0                                                  │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ AssemblyAI (Transcrição Cloud)            ✅ Ativo    │    │
│  │ Cloud                                                   │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ℹ️ Informações do Sistema                                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Versão          2.0.0                                   │    │
│  │ API Backend     http://localhost:2020                   │    │
│  │ Status da API   🟢 Online                              │    │
│  │ Banco de Dados  connected                               │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## 🎨 Paleta de Cores

```
┌─────────────────────────────────────────────┐
│ Primárias                                   │
├─────────────────────────────────────────────┤
│ 🟣 Primary     #8b5cf6  (Purple)           │
│ ⚪ White       #ffffff                      │
│ ⚫ Black       #000000                      │
│ 🔵 Gray-50     #f9fafb  (Background)       │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Status                                      │
├─────────────────────────────────────────────┤
│ 🟢 Success     #10b981  (Green)            │
│ 🟡 Warning     #f59e0b  (Yellow)           │
│ 🔴 Error       #ef4444  (Red)              │
│ 🔵 Info        #3b82f6  (Blue)             │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Text                                        │
├─────────────────────────────────────────────┤
│ ⚫ Primary     #111827  (Gray-900)         │
│ 🔘 Secondary   #6b7280  (Gray-500)         │
│ ⚪ Muted       #9ca3af  (Gray-400)         │
└─────────────────────────────────────────────┘
```

## 🔔 Notificações (Toasts)

```
┌────────────────────────────────────────┐
│ ✅ Sucesso                             │
│ Transcrição concluída com sucesso!    │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ ⚠️ Aviso                               │
│ Arquivo muito grande! Máx: 100MB      │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ ❌ Erro                                │
│ Erro ao processar arquivo             │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ ℹ️ Informação                          │
│ Upload em progresso...                │
└────────────────────────────────────────┘
```

## 🎯 Estados de Loading

```
┌────────────────────────────────┐
│                                │
│          ⭕ (spinning)         │
│                                │
│      Carregando dados...      │
│                                │
└────────────────────────────────┘
```

## 📦 Estados Vazios

```
┌────────────────────────────────┐
│                                │
│        📁 (ícone grande)       │
│                                │
│  Nenhuma transcrição ainda    │
│                                │
│    [Criar Nova Transcrição]   │
│                                │
└────────────────────────────────┘
```

## 🔄 Estados de Progresso

```
┌────────────────────────────────────────┐
│ 🎵 meu_audio.mp3                       │
│ 15.5 MB                                │
│                                         │
│ Processando...              45%        │
│ ████████████░░░░░░░░░░░░░              │
└────────────────────────────────────────┘
```

## 📱 Responsividade

### Mobile (< 768px)
```
┌────────────────┐
│  🎙️ ☰  UD     │ ← Navbar compacta
├────────────────┤
│                │
│   Conteúdo    │
│   Stack       │
│   Vertical    │
│                │
└────────────────┘
```

### Tablet (768px - 1024px)
```
┌─────┬──────────┐
│  🎙️ │    UD    │
├─────┼──────────┤
│ ☰   │          │
│     │ Conteúdo │
│     │          │
└─────┴──────────┘
```

### Desktop (> 1024px)
```
┌────────┬─────────────────┐
│  🎙️    │          UD     │
├────────┼─────────────────┤
│        │                 │
│ Menu   │   Conteúdo     │
│ Full   │   Expandido    │
│        │                 │
└────────┴─────────────────┘
```

## 🎭 Animações

- **Fade In**: Entrada suave de componentes
- **Slide In**: Sidebar e modais
- **Pulse**: Loading spinners
- **Bounce**: Confirmações
- **Shimmer**: Skeleton loading

## 🖱️ Interações

### Botões
```
Normal:     [  Botão  ]
Hover:      [  Botão  ] ← cor mais escura
Active:     [  Botão  ] ← pressed state
Disabled:   [  Botão  ] ← opacidade 50%
Loading:    [ ⭕ ...  ] ← spinner
```

### Cards
```
Normal:     ┌─────┐
            │     │
            └─────┘

Hover:      ┌─────┐
            │ ▲   │ ← shadow aumenta
            └─────┘
```

### Links
```
Normal:     Link
Hover:      Link ← sublinhado
Active:     Link ← cor primária
```

## 🌐 Navegação

```
Início (/)
  ├─ Nova Transcrição (/new-transcription)
  ├─ Transcrições (/transcriptions)
  │   └─ Detalhes (/transcriptions/:id)
  └─ Configurações (/settings)
```

## 🔐 Fluxo de Autenticação (Futuro)

```
1. Login
   ↓
2. Verificar Token
   ↓
3. ✅ Válido → Dashboard
   ❌ Inválido → Login
```

## 📊 Métricas Visuais

```
Dashboard Cards:
┌─────────────────┐  ┌─────────────────┐
│  📊             │  │  ✅             │
│  Total          │  │  Concluídas     │
│  15             │  │  12             │
└─────────────────┘  └─────────────────┘

┌─────────────────┐  ┌─────────────────┐
│  ⏱️             │  │  ❌             │
│  Processando    │  │  Falhadas       │
│  2              │  │  1              │
└─────────────────┘  └─────────────────┘
```

Esta documentação visual serve como referência rápida para o design e layout do frontend! 🎨
