import streamlit as st
import requests
from pydub import AudioSegment
import os
import subprocess

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except FileNotFoundError:
        st.error("FFmpeg não encontrado. Instale o FFmpeg e adicione ao PATH.")
        st.stop()

def check_service_health(url):
    try:
        response = requests.get(f"{url}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        return True, f"{data['model']} ({data['device']})"
    except requests.exceptions.RequestException as e:
        return False, f"Erro: {str(e)}"

def convert_to_wav(input_path, output_path="audio.wav"):
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="wav")
        return output_path
    except Exception as e:
        st.error(f"Erro ao converter arquivo de áudio: {str(e)}")
        st.stop()

check_ffmpeg()

st.title("Transcrição de Áudio/Vídeo")

st.subheader("Status dos Modelos")
whisper_ok, whisper_status = check_service_health("http://localhost:8000")
assemblyai_ok, assemblyai_status = check_service_health("http://localhost:8002")
pyannote_ok, pyannote_status = check_service_health("http://localhost:8001")

st.write(f"Whisper: {'Disponível' if whisper_ok else 'Indisponível'} - {whisper_status}")
st.write(f"AssemblyAI: {'Disponível' if assemblyai_ok else 'Indisponível'} - {assemblyai_status}")
st.write(f"Pyannote: {'Disponível' if pyannote_ok else 'Indisponível'} - {pyannote_status}")

# Verificar se pelo menos um serviço de transcrição está disponível
if whisper_ok or assemblyai_ok:
    # Criar lista de modelos disponíveis para o selectbox
    available_models = []
    if whisper_ok:
        available_models.append("Whisper (local)")
    if assemblyai_ok:
        available_models.append("AssemblyAI (cloud)")

    uploaded_file = st.file_uploader("Escolha um arquivo de áudio ou vídeo", type=["mp3", "wav", "mp4", "mpeg"])
    use_diarization = st.checkbox("Incluir segmentação de falantes", value=True, disabled=not pyannote_ok)
    
    # Mostrar selectbox apenas se houver mais de um modelo disponível
    if len(available_models) > 1:
        transcription_model = st.selectbox("Escolher modelo de transcrição", available_models)
    else:
        transcription_model = available_models[0]
        st.write(f"Modelo de transcrição: {transcription_model}")

    if uploaded_file:
        with st.spinner("Processando o arquivo..."):
            # Salvar arquivo temporário
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())

            # Converter para WAV
            audio_path = convert_to_wav(temp_path)

            # Obter duração total do áudio
            audio = AudioSegment.from_file(audio_path)
            total_duration = len(audio) / 1000.0  # Duração em segundos

            if use_diarization:
                if not pyannote_ok:
                    st.error("Segmentação de falantes requer o serviço Pyannote ativo.")
                    st.stop()

                st.info("A diarização pode levar vários minutos para arquivos longos ou em CPUs mais lentas. Por favor, aguarde.")
                try:
                    with st.spinner("Realizando diarização (pode levar até 10 minutos)..."):
                        with open(audio_path, "rb") as f:
                            diarization_response = requests.post(
                                "http://localhost:8001/diarize",
                                files={"file": f},
                                timeout=600  # 10 minutos
                            )
                            diarization_response.raise_for_status()
                    result = diarization_response.json()
                    segments = result["segments"]
                    num_speakers = result["num_speakers"]
                except requests.exceptions.RequestException as e:
                    st.warning(f"Erro na diarização: {str(e)}. Continuando sem segmentação de falantes.")
                    segments = [{"start": 0, "end": total_duration, "speaker": "Unknown"}]
                    num_speakers = 1

                if segments:  # Verificar se há segmentos para processar
                    st.write(f"Número de falantes detectados: {num_speakers}")
                    st.write("Transcrições por segmento:")

                    # Escolher serviço com base no modelo selecionado
                    service_url = "http://localhost:8000" if transcription_model == "Whisper (local)" else "http://localhost:8002"

                    for segment in segments:
                        # Tratar end como total_duration se for None
                        end_time = segment["end"] if segment["end"] is not None else total_duration
                        with st.spinner(f"Transcrevendo segmento {segment['speaker']} ({segment['start']:.1f}s - {end_time:.1f}s)..."):
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
                                st.write(f"Speaker {segment['speaker']} ({segment['start']:.1f}s - {end_time:.1f}s): {transcription}")
                            except requests.exceptions.RequestException as e:
                                st.error(f"Erro na transcrição do segmento {segment['speaker']}: {str(e)}")
            else:
                # Escolher serviço com base no modelo selecionado
                service_url = "http://localhost:8000" if transcription_model == "Whisper (local)" else "http://localhost:8002"
                
                try:
                    with st.spinner("Transcrevendo áudio..."):
                        with open(audio_path, "rb") as f:
                            transcription_response = requests.post(
                                f"{service_url}/transcribe_segment",
                                files={"file": f},
                                timeout=120
                            )
                            transcription_response.raise_for_status()
                    transcription = transcription_response.json()["transcription"]
                    st.write("Transcrição:", transcription)
                except requests.exceptions.RequestException as e:
                    st.error(f"Erro na transcrição: {str(e)}")

            # Limpar arquivos temporários
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(audio_path):
                os.remove(audio_path)
else:
    st.warning("Pelo menos um dos modelos de transcrição (Whisper ou AssemblyAI) precisa estar disponível para prosseguir. Inicie um dos serviços correspondentes.")