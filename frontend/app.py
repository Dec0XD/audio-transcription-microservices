import streamlit as st
import requests
from pydub import AudioSegment
import os
import subprocess
import json
import time
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from io import BytesIO
import base64

# Configuração da página
st.set_page_config(
    page_title="🎙️ Transcritor AI",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para melhorar a aparência
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .service-card {
        background: black;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
    
    .service-card.available {
        border-left-color: #28a745;
    }
    
    .service-card.unavailable {
        border-left-color: #dc3545;
    }
    
    .result-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
    
    .speaker-segment {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .stats-container {
        display: flex;
        justify-content: space-around;
        margin: 1rem 0;
    }
    
    .stat-item {
        text-align: center;
        padding: 1rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        min-width: 120px;
    }
</style>
""", unsafe_allow_html=True)

def check_ffmpeg():
    """Verifica se o FFmpeg está instalado"""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except FileNotFoundError:
        return False

def check_service_health(url, service_name):
    """Verifica a saúde de um serviço"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        return True, f"{data.get('model', 'N/A')} ({data.get('device', 'N/A')})"
    except requests.exceptions.RequestException as e:
        return False, f"Erro: {str(e)}"

def convert_to_wav(input_path, output_path="audio.wav"):
    """Converte arquivo de áudio para WAV"""
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="wav")
        return output_path, len(audio) / 1000.0  # Retorna também a duração
    except Exception as e:
        st.error(f"Erro ao converter arquivo de áudio: {str(e)}")
        return None, 0

def create_audio_waveform(audio_path):
    """Cria visualização da forma de onda do áudio"""
    try:
        audio = AudioSegment.from_file(audio_path)
        samples = audio.get_array_of_samples()
        
        # Reduzir amostragem para visualização
        step = max(1, len(samples) // 1000)
        samples_reduced = samples[::step]
        
        # Criar timestamps
        duration = len(audio) / 1000.0
        timestamps = [i * duration / len(samples_reduced) for i in range(len(samples_reduced))]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=samples_reduced,
            mode='lines',
            name='Forma de Onda',
            line=dict(color='#667eea', width=1)
        ))
        
        fig.update_layout(
            title="Visualização do Áudio",
            xaxis_title="Tempo (s)",
            yaxis_title="Amplitude",
            height=200,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        return fig
    except Exception as e:
        st.error(f"Erro ao criar visualização: {str(e)}")
        return None

def save_transcription_history(filename, transcription_data):
    """Salva histórico de transcrições"""
    history_file = "transcription_history.json"
    
    # Carregar histórico existente
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            history = []
    
    # Adicionar nova transcrição
    history.append({
        "timestamp": datetime.now().isoformat(),
        "filename": filename,
        "data": transcription_data
    })
    
    # Manter apenas os últimos 50 registros
    history = history[-50:]
    
    # Salvar histórico atualizado
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def load_transcription_history():
    """Carrega histórico de transcrições"""
    history_file = "transcription_history.json"
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def create_download_link(content, filename, file_type="text"):
    """Cria link de download para conteúdo"""
    if file_type == "json":
        content = json.dumps(content, ensure_ascii=False, indent=2)
        mime_type = "application/json"
    else:
        mime_type = "text/plain"
    
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}">📥 Baixar {filename}</a>'
    return href

# Verificar FFmpeg
if not check_ffmpeg():
    st.error("⚠️ FFmpeg não encontrado. Instale o FFmpeg e adicione ao PATH.")
    st.info("💡 **Como instalar FFmpeg:**")
    st.code("sudo apt update && sudo apt install ffmpeg")
    st.stop()

# Header principal
st.markdown("""
<div class="main-header">
    <h1>🎙️ Transcritor AI</h1>
    <p>Sistema Inteligente de Transcrição de Áudio e Vídeo</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Configurações de qualidade
    st.subheader("Qualidade da Transcrição")
    quality_mode = st.selectbox(
        "Modo de Qualidade",
        ["Rápido", "Balanceado", "Alta Qualidade"],
        index=1
    )
    
    # Configurações de idioma
    language = st.selectbox(
        "Idioma Principal",
        ["Português", "Inglês", "Espanhol", "Francês", "Auto-detectar"],
        index=0
    )
    
    # Configurações avançadas
    st.subheader("Configurações Avançadas")
    enable_timestamps = st.checkbox("Incluir timestamps", value=True)
    enable_confidence = st.checkbox("Mostrar confiança", value=False)
    
    # Histórico
    st.subheader("📚 Histórico")
    history = load_transcription_history()
    if history:
        st.write(f"Total de transcrições: {len(history)}")
        if st.button("Limpar Histórico"):
            if os.path.exists("transcription_history.json"):
                os.remove("transcription_history.json")
            st.success("Histórico limpo!")
            st.rerun()
    else:
        st.write("Nenhuma transcrição no histórico")

# Área principal
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🔍 Status dos Serviços")
    
    # Verificar status dos serviços
    services = [
        ("Whisper (Local)", "http://localhost:8000", "🤖"),
        ("AssemblyAI (Cloud)", "http://localhost:8002", "☁️"),
        ("Pyannote (Diarização)", "http://localhost:8001", "👥")
    ]
    
    service_status = {}
    
    for service_name, url, icon in services:
        is_available, status_info = check_service_health(url, service_name)
        service_status[service_name] = is_available
        
        status_class = "available" if is_available else "unavailable"
        status_text = "Disponível" if is_available else "Indisponível"
        status_color = "🟢" if is_available else "🔴"
        
        st.markdown(f"""
        <div class="service-card {status_class}">
            <h4>{icon} {service_name} {status_color}</h4>
            <p><strong>Status:</strong> {status_text}</p>
            <p><strong>Detalhes:</strong> {status_info}</p>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.header("📊 Estatísticas")
    
    # Estatísticas do histórico
    if history:
        total_files = len(history)
        recent_files = len([h for h in history if (datetime.now() - datetime.fromisoformat(h['timestamp'])).days < 7])
        
        st.markdown(f"""
        <div class="stats-container">
            <div class="stat-item">
                <h3>{total_files}</h3>
                <p>Total de Arquivos</p>
            </div>
            <div class="stat-item">
                <h3>{recent_files}</h3>
                <p>Esta Semana</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Verificar se pelo menos um serviço de transcrição está disponível
transcription_services = ["Whisper (Local)", "AssemblyAI (Cloud)"]
available_transcription = [s for s in transcription_services if service_status.get(s, False)]

# Área de upload
st.header("📁 Upload de Arquivo")

if not available_transcription:
    st.warning("⚠️ Nenhum serviço de transcrição está disponível. Inicie pelo menos um dos serviços (Whisper ou AssemblyAI) para continuar.")
    st.info("💡 **Como iniciar os serviços:**")
    st.code("""
# Para Whisper (local)
python whisper_service.py

# Para AssemblyAI (cloud)  
python assemblyai_service.py

# Para Pyannote (diarização)
python pyannote_service.py
    """)
else:
    uploaded_file = st.file_uploader(
        "Escolha um arquivo de áudio ou vídeo",
        type=["mp3", "wav", "mp4", "mpeg", "m4a", "flac"],
        help="Formatos suportados: MP3, WAV, MP4, MPEG, M4A, FLAC"
    )

    if uploaded_file:
        # Mostrar informações do arquivo sem carregar tudo em memória
        # Preferir atributo .size quando disponível (bytes)
        try:
            file_size_bytes = uploaded_file.size
        except Exception:
            try:
                file_size_bytes = len(uploaded_file.getbuffer())
            except Exception:
                # Último recurso: ler e resetar (poderá consumir memória)
                file_content = uploaded_file.read()
                file_size_bytes = len(file_content)
                uploaded_file.seek(0)

        file_size = file_size_bytes / (1024 * 1024)  # MB

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Nome do Arquivo", uploaded_file.name)
        with col2:
            st.metric("Tamanho", f"{file_size:.2f} MB")
        with col3:
            estimated_time = max(1, int(file_size * 0.5))  # Estimativa simples
            st.metric("Tempo Estimado", f"~{estimated_time} min")

    # Configurações de transcrição
    st.header("🎛️ Configurações de Transcrição")

    col1, col2 = st.columns(2)

    with col1:
        # Seleção do modelo
        if len(available_transcription) > 1:
            transcription_model = st.selectbox(
                "Modelo de Transcrição",
                available_transcription,
                help="Whisper é mais rápido (local), AssemblyAI tem maior precisão (cloud)"
            )
        elif len(available_transcription) == 1:
            transcription_model = available_transcription[0]
            st.info(f"Modelo selecionado: {transcription_model}")
        else:
            transcription_model = None
            st.warning("Nenhum modelo disponível")

    with col2:
        # Opção de diarização
        use_diarization = st.checkbox(
            "Segmentação de Falantes",
            value=service_status.get("Pyannote (Diarização)", False),
            disabled=not service_status.get("Pyannote (Diarização)", False),
            help="Identifica diferentes falantes no áudio (requer Pyannote)"
        )

    # Processamento
    if uploaded_file and transcription_model and st.button("🚀 Iniciar Transcrição", type="primary"):
        start_time = time.time()
        
        with st.spinner("Processando arquivo..."):
            # Salvar arquivo temporário por streaming (chunks) para evitar usar muita memória
            temp_path = f"temp_{uploaded_file.name}"
            CHUNK_SIZE = 4 * 1024 * 1024  # 4MB
            uploaded_file.seek(0)
            with open(temp_path, "wb") as f:
                while True:
                    chunk = uploaded_file.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
            # Garantir ponteiro no início
            uploaded_file.seek(0)
            
            # Converter para WAV
            audio_path, duration = convert_to_wav(temp_path)
            
            if audio_path:
                # Mostrar visualização do áudio
                st.subheader("🌊 Visualização do Áudio")
                waveform_fig = create_audio_waveform(audio_path)
                if waveform_fig:
                    st.plotly_chart(waveform_fig, use_container_width=True)
                
                # Preparar dados para salvar no histórico
                transcription_data = {
                    "filename": uploaded_file.name,
                    "duration": duration,
                    "model": transcription_model,
                    "diarization": use_diarization,
                    "segments": []
                }
                
                if use_diarization and service_status.get("Pyannote (Diarização)", False):
                    st.info("🔄 Realizando diarização (pode levar alguns minutos)...")
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        with open(audio_path, "rb") as f:
                            status_text.text("Analisando falantes...")
                            progress_bar.progress(25)
                            
                            diarization_response = requests.post(
                                "http://localhost:8001/diarize",
                                files={"file": f},
                                timeout=600
                            )
                            diarization_response.raise_for_status()
                        
                        progress_bar.progress(50)
                        result = diarization_response.json()
                        segments = result["segments"]
                        num_speakers = result["num_speakers"]
                        
                        st.success(f"✅ Detectados {num_speakers} falantes")
                        
                        # Escolher serviço de transcrição
                        service_url = "http://localhost:8000" if transcription_model == "Whisper (Local)" else "http://localhost:8002"
                        
                        st.subheader("📝 Transcrições por Segmento")
                        
                        for i, segment in enumerate(segments):
                            progress = 50 + (i + 1) * 50 / len(segments)
                            progress_bar.progress(int(progress))
                            status_text.text(f"Transcrevendo segmento {i+1}/{len(segments)}...")
                            
                            end_time = segment["end"] if segment["end"] is not None else duration
                            
                            try:
                                with open(audio_path, "rb") as f:
                                    transcription_response = requests.post(
                                        f"{service_url}/transcribe_segment",
                                        files={"file": (audio_path, f, "audio/wav")},
                                        params={"start": segment["start"], "end": segment["end"]},
                                        timeout=120
                                    )
                                    transcription_response.raise_for_status()
                                
                                transcription = transcription_response.json()["transcription"]
                                
                                # Adicionar ao histórico
                                transcription_data["segments"].append({
                                    "speaker": segment["speaker"],
                                    "start": segment["start"],
                                    "end": end_time,
                                    "text": transcription
                                })
                                
                                # Mostrar resultado
                                st.markdown(f"""
                                <div class="speaker-segment">
                                    <h5>🗣️ Falante {segment['speaker']}</h5>
                                    <p><strong>Tempo:</strong> {segment['start']:.1f}s - {end_time:.1f}s</p>
                                    <p><strong>Transcrição:</strong> {transcription}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                            except requests.exceptions.RequestException as e:
                                st.error(f"Erro na transcrição do segmento {segment['speaker']}: {str(e)}")
                        
                        progress_bar.progress(100)
                        status_text.text("Concluído!")
                        
                    except requests.exceptions.RequestException as e:
                        st.warning(f"Erro na diarização: {str(e)}. Continuando sem segmentação.")
                        use_diarization = False
                
                if not use_diarization:
                    # Transcrição simples sem diarização
                    service_url = "http://localhost:8000" if transcription_model == "Whisper (Local)" else "http://localhost:8002"
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        status_text.text("Transcrevendo áudio...")
                        progress_bar.progress(50)
                        
                        with open(audio_path, "rb") as f:
                            transcription_response = requests.post(
                                f"{service_url}/transcribe_segment",
                                files={"file": f},
                                timeout=120
                            )
                            transcription_response.raise_for_status()
                        
                        progress_bar.progress(100)
                        transcription = transcription_response.json()["transcription"]
                        
                        # Adicionar ao histórico
                        transcription_data["segments"].append({
                            "speaker": "Único",
                            "start": 0,
                            "end": duration,
                            "text": transcription
                        })
                        
                        st.subheader("📝 Transcrição Completa")
                        st.markdown(f"""
                        <div class="result-card">
                            <h4>Resultado da Transcrição</h4>
                            <p>{transcription}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        status_text.text("Concluído!")
                        
                    except requests.exceptions.RequestException as e:
                        st.error(f"Erro na transcrição: {str(e)}")
                
                # Salvar no histórico
                save_transcription_history(uploaded_file.name, transcription_data)
                
                # Estatísticas finais
                processing_time = time.time() - start_time
                word_count = sum(len(seg["text"].split()) for seg in transcription_data["segments"])
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Duração do Áudio", f"{duration:.1f}s")
                with col2:
                    st.metric("Tempo de Processamento", f"{processing_time:.1f}s")
                with col3:
                    st.metric("Palavras Transcritas", word_count)
                with col4:
                    st.metric("Falantes", len(set(seg["speaker"] for seg in transcription_data["segments"])))
                
                # Opções de download
                st.subheader("💾 Download dos Resultados")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Download como texto
                    text_content = "\n\n".join([
                        f"Falante {seg['speaker']} ({seg['start']:.1f}s - {seg['end']:.1f}s):\n{seg['text']}"
                        for seg in transcription_data["segments"]
                    ])
                    st.markdown(
                        create_download_link(text_content, f"{uploaded_file.name}_transcricao.txt"),
                        unsafe_allow_html=True
                    )
                
                with col2:
                    # Download como JSON
                    st.markdown(
                        create_download_link(transcription_data, f"{uploaded_file.name}_transcricao.json", "json"),
                        unsafe_allow_html=True
                    )
                
                with col3:
                    # Download como SRT (legendas)
                    srt_content = ""
                    for i, seg in enumerate(transcription_data["segments"], 1):
                        start_time = f"{int(seg['start']//3600):02d}:{int((seg['start']%3600)//60):02d}:{seg['start']%60:06.3f}".replace('.', ',')
                        end_time = f"{int(seg['end']//3600):02d}:{int((seg['end']%3600)//60):02d}:{seg['end']%60:06.3f}".replace('.', ',')
                        srt_content += f"{i}\n{start_time} --> {end_time}\n{seg['text']}\n\n"
                    
                    st.markdown(
                        create_download_link(srt_content, f"{uploaded_file.name}_legendas.srt"),
                        unsafe_allow_html=True
                    )
                
                # Limpar arquivos temporários
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                
                st.success("🎉 Transcrição concluída com sucesso!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🎙️ Transcritor AI - Sistema Inteligente de Transcrição</p>
    <p>Desenvolvido com Streamlit • Whisper • AssemblyAI • Pyannote</p>
</div>
""", unsafe_allow_html=True)

