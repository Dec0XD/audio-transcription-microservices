import api from './api'

export const audioService = {
  // Verificar saúde do backend
  async checkHealth() {
    const { data } = await api.get('/health')
    return data
  },

  // Upload e transcrição de áudio
  async transcribeAudio(file, options = {}) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('use_diarization', options.useDiarization || false)
    
    if (options.transcriptionModel) {
      formData.append('transcription_model', options.transcriptionModel)
    }

    const { data } = await api.post('/transcribe', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: options.onUploadProgress,
    })
    
    return data
  },

  // Listar transcrições
  async listTranscriptions(params = {}) {
    const { data } = await api.get('/transcriptions', { params })
    return data
  },

  // Obter detalhes de uma transcrição
  async getTranscription(id) {
    const { data } = await api.get(`/transcriptions/${id}`)
    return data
  },

  // Deletar transcrição
  async deleteTranscription(id) {
    const { data } = await api.delete(`/transcriptions/${id}`)
    return data
  },

  // Obter estatísticas
  async getStats() {
    const { data } = await api.get('/stats')
    return data
  },

  // Diarização direta
  async diarizeAudio(file, options = {}) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('min_duration', options.minDuration || 0.7)
    formData.append('silence_threshold', options.silenceThreshold || -30)

    const { data } = await api.post('/diarize', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    
    return data
  },
}
