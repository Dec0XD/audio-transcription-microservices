// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:2020'

// Application Info
export const APP_NAME = 'Transcritor AI'
export const APP_VERSION = '2.0.0'
export const APP_DESCRIPTION = 'Sistema Inteligente de Transcrição de Áudio e Vídeo'

// File Upload Configuration
export const ALLOWED_FILE_TYPES = [
  'audio/mpeg',
  'audio/wav',
  'audio/mp4',
  'audio/x-m4a',
  'audio/flac',
  'audio/ogg',
  'audio/opus',
  'video/mp4'
]

export const ALLOWED_FILE_EXTENSIONS = ['.mp3', '.wav', '.mp4', '.m4a', '.flac', '.ogg', '.opus']
export const MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024 // 5GB in bytes (alinhado com backend)

// Transcription Models
export const TRANSCRIPTION_MODELS = {
  WHISPER: 'whisper',
  ASSEMBLYAI: 'assemblyai'
}

export const MODEL_INFO = {
  [TRANSCRIPTION_MODELS.WHISPER]: {
    name: 'Whisper',
    description: 'Modelo local, mais rápido',
    icon: '🎙️',
    type: 'local'
  },
  [TRANSCRIPTION_MODELS.ASSEMBLYAI]: {
    name: 'AssemblyAI',
    description: 'Modelo cloud, maior precisão',
    icon: '☁️',
    type: 'cloud'
  }
}

// Status Types
export const TRANSCRIPTION_STATUS = {
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed'
}

export const STATUS_COLORS = {
  [TRANSCRIPTION_STATUS.PROCESSING]: {
    bg: 'bg-yellow-100',
    text: 'text-yellow-800',
    badge: 'badge-warning'
  },
  [TRANSCRIPTION_STATUS.COMPLETED]: {
    bg: 'bg-green-100',
    text: 'text-green-800',
    badge: 'badge-success'
  },
  [TRANSCRIPTION_STATUS.FAILED]: {
    bg: 'bg-red-100',
    text: 'text-red-800',
    badge: 'badge-error'
  }
}

// Pagination
export const DEFAULT_PAGE_SIZE = 10
export const PAGE_SIZE_OPTIONS = [5, 10, 20, 50]

// Date Formats
export const DATE_FORMAT = 'dd/MM/yyyy'
export const DATETIME_FORMAT = 'dd/MM/yyyy HH:mm'
export const TIME_FORMAT = 'HH:mm:ss'

// Local Storage Keys
export const STORAGE_KEYS = {
  AUTH: 'auth-storage',
  THEME: 'theme-preference',
  LANGUAGE: 'language-preference'
}

// Routes
export const ROUTES = {
  HOME: '/',
  DASHBOARD: '/',
  NEW_TRANSCRIPTION: '/new-transcription',
  TRANSCRIPTIONS: '/transcriptions',
  TRANSCRIPTION_DETAIL: '/transcriptions/:id',
  SETTINGS: '/settings'
}

// Toast Configuration
export const TOAST_CONFIG = {
  position: 'top-right',
  duration: 4000,
  success: { duration: 3000 },
  error: { duration: 5000 }
}

// Export Formats
export const EXPORT_FORMATS = {
  TXT: 'txt',
  JSON: 'json',
  SRT: 'srt',
  VTT: 'vtt'
}

export const FORMAT_INFO = {
  [EXPORT_FORMATS.TXT]: {
    name: 'Texto',
    extension: '.txt',
    mimeType: 'text/plain',
    icon: '📄'
  },
  [EXPORT_FORMATS.JSON]: {
    name: 'JSON',
    extension: '.json',
    mimeType: 'application/json',
    icon: '📊'
  },
  [EXPORT_FORMATS.SRT]: {
    name: 'Legendas SRT',
    extension: '.srt',
    mimeType: 'text/plain',
    icon: '📝'
  },
  [EXPORT_FORMATS.VTT]: {
    name: 'Legendas VTT',
    extension: '.vtt',
    mimeType: 'text/vtt',
    icon: '📹'
  }
}
