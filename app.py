import streamlit as st
import os
import uuid
import requests
from gtts import gTTS
import tempfile
import json
from io import BytesIO

# 페이지 설정
st.set_page_config(
    page_title="🎤 SWING AI Voice Studio",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 환경변수 및 secrets 설정
ELEVENLABS_API_KEY = st.secrets.get("ELEVENLABS_API_KEY", os.getenv('ELEVENLABS_API_KEY'))
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv('OPENAI_API_KEY'))

class TTSGenerator:
    def __init__(self):
        self.elevenlabs_headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }

        self.openai_headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        # 일레븐랩스 음성 목록
        self.elevenlabs_voices = [
            {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "gender": "female", "accent": "American"},
            {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "gender": "female", "accent": "American"},
            {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "gender": "female", "accent": "American"},
            {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "gender": "male", "accent": "American"},
            {"id": "MF3mGyEYCl7XYWbV9V6O", "name": "Elli", "gender": "female", "accent": "American"},
            {"id": "TxGEqnHWrfWFTfGW9XjX", "name": "Josh", "gender": "male", "accent": "American"},
            {"id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "gender": "male", "accent": "American"},
            {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "gender": "male", "accent": "American"},
            {"id": "yoZ06aMxZJJ28mfd3POQ", "name": "Sam", "gender": "male", "accent": "American"}
        ]

        # OpenAI TTS 음성 목록
        self.openai_voices = [
            {"id": "alloy", "name": "Alloy", "description": "균형 잡힌 중성적 음성"},
            {"id": "echo", "name": "Echo", "description": "남성적이고 깊은 음성"},
            {"id": "fable", "name": "Fable", "description": "따뜻하고 친근한 음성"},
            {"id": "onyx", "name": "Onyx", "description": "강렬하고 카리스마 있는 음성"},
            {"id": "nova", "name": "Nova", "description": "활기차고 현대적인 음성"},
            {"id": "shimmer", "name": "Shimmer", "description": "부드럽고 우아한 음성"}
        ]

        # OpenAI TTS 모델 목록
        self.openai_models = [
            {"id": "tts-1", "name": "TTS-1 (빠름)", "description": "빠른 처리, 기본 품질"},
            {"id": "tts-1-hd", "name": "TTS-1-HD (고품질)", "description": "높은 품질, 약간 느림"}
        ]

        # OpenAI TTS 오디오 포맷
        self.openai_formats = [
            {"id": "mp3", "name": "MP3", "description": "호환성 최고"},
            {"id": "opus", "name": "OPUS", "description": "인터넷 스트리밍 최적화"},
            {"id": "aac", "name": "AAC", "description": "Apple 기기 최적화"},
            {"id": "flac", "name": "FLAC", "description": "무손실 압축"}
        ]

        # 일레븐랩스 모델 목록
        self.elevenlabs_models = [
            {"id": "eleven_monolingual_v1", "name": "English v1"},
            {"id": "eleven_multilingual_v1", "name": "Multilingual v1"},
            {"id": "eleven_multilingual_v2", "name": "Multilingual v2"},
            {"id": "eleven_turbo_v2", "name": "Turbo v2 (Fast)"}
        ]

        # 구글 TTS 언어 목록
        self.google_languages = [
            {"code": "ko", "name": "🇰🇷 한국어"},
            {"code": "en", "name": "🇺🇸 English"},
            {"code": "ja", "name": "🇯🇵 日本語"},
            {"code": "zh", "name": "🇨🇳 中文"},
            {"code": "es", "name": "🇪🇸 Español"},
            {"code": "fr", "name": "🇫🇷 Français"},
            {"code": "de", "name": "🇩🇪 Deutsch"},
            {"code": "it", "name": "🇮🇹 Italiano"},
            {"code": "pt", "name": "🇵🇹 Português"},
            {"code": "ru", "name": "🇷🇺 Русский"}
        ]

    def generate_google_tts(self, text, settings):
        """구글 TTS로 음성 생성"""
        try:
            lang = settings.get('language', 'ko')
            slow = settings.get('slow', False)

            tts = gTTS(text=text, lang=lang, slow=slow)
            audio_buffer = BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)

            return {
                "success": True,
                "audio_data": audio_buffer.read(),
                "service": f"Google TTS ({lang.upper()})",
                "settings": settings,
                "filename": f"google_tts_{lang}.mp3"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "service": "Google TTS"
            }

    def generate_elevenlabs_tts(self, text, settings):
        """일레븐랩스 TTS로 음성 생성"""
        try:
            if not ELEVENLABS_API_KEY:
                return {
                    "success": False,
                    "error": "ElevenLabs API 키가 설정되지 않았습니다",
                    "service": "ElevenLabs"
                }

            voice_id = settings.get('voice_id', self.elevenlabs_voices[0]["id"])
            model_id = settings.get('model_id', 'eleven_multilingual_v2')
            stability = float(settings.get('stability', 0.5))
            similarity_boost = float(settings.get('similarity_boost', 0.5))
            style = float(settings.get('style', 0.0))
            use_speaker_boost = settings.get('use_speaker_boost', True)

            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

            data = {
                "text": text,
                "model_id": model_id,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                    "style": style,
                    "use_speaker_boost": use_speaker_boost
                }
            }

            response = requests.post(url, json=data, headers=self.elevenlabs_headers)

            if response.status_code == 200:
                voice_name = next((v["name"] for v in self.elevenlabs_voices if v["id"] == voice_id), "Unknown")
                model_name = next((m["name"] for m in self.elevenlabs_models if m["id"] == model_id), "Unknown")

                return {
                    "success": True,
                    "audio_data": response.content,
                    "service": f"ElevenLabs ({voice_name} - {model_name})",
                    "settings": settings,
                    "filename": f"elevenlabs_{voice_name.lower()}.mp3"
                }
            else:
                error_msg = f"API Error: {response.status_code}"
                if response.status_code == 401:
                    error_msg += " - API 키를 확인해주세요"
                elif response.status_code == 429:
                    error_msg += " - 사용량 한도를 초과했습니다"
                elif response.status_code == 422:
                    error_msg += " - 텍스트가 너무 길거나 잘못된 설정입니다"

                return {
                    "success": False,
                    "error": error_msg,
                    "service": "ElevenLabs"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "service": "ElevenLabs"
            }

    def generate_openai_tts(self, text, settings):
        """OpenAI TTS로 음성 생성"""
        try:
            if not OPENAI_API_KEY:
                return {
                    "success": False,
                    "error": "OpenAI API 키가 설정되지 않았습니다",
                    "service": "OpenAI TTS"
                }

            voice = settings.get('voice', 'alloy')
            model = settings.get('model', 'tts-1')
            speed = float(settings.get('speed', 1.0))
            audio_format = settings.get('response_format', 'mp3')

            url = "https://api.openai.com/v1/audio/speech"

            data = {
                "model": model,
                "input": text,
                "voice": voice,
                "speed": speed,
                "response_format": audio_format
            }

            response = requests.post(url, json=data, headers=self.openai_headers)

            if response.status_code == 200:
                voice_name = next((v["name"] for v in self.openai_voices if v["id"] == voice), voice)
                model_name = next((m["name"] for m in self.openai_models if m["id"] == model), model)

                return {
                    "success": True,
                    "audio_data": response.content,
                    "service": f"OpenAI TTS ({voice_name} - {model_name})",
                    "settings": settings,
                    "filename": f"openai_{voice}_{model}.{audio_format}"
                }
            else:
                error_msg = f"OpenAI API Error: {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg += f" - {error_data['error'].get('message', 'Unknown error')}"
                except:
                    pass

                return {
                    "success": False,
                    "error": error_msg,
                    "service": "OpenAI TTS"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"연결 오류: {str(e)}",
                "service": "OpenAI TTS"
            }

# TTS 생성기 인스턴스 생성
@st.cache_resource
def get_tts_generator():
    return TTSGenerator()

tts_generator = get_tts_generator()

# 세션 상태 초기화
if 'generated_audios' not in st.session_state:
    st.session_state.generated_audios = []
if 'total_generated' not in st.session_state:
    st.session_state.total_generated = 0

# 원본 HTML의 neumorphism CSS 완전 적용
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        /* Neumorphism 색상 팔레트 */
        --primary: #4f46e5;
        --secondary: #6366f1;
        --accent: #8b5cf6;
        --accent-light: #a78bfa;
        --openai: #10b981;
        --openai-dark: #059669;
        --success: #22c55e;
        --warning: #f59e0b;
        --error: #ef4444;

        /* Neumorphism 배경 및 표면 */
        --background: #e0e7ff;
        --surface: #e0e7ff;
        --surface-light: #f1f5f9;
        --surface-dark: #cbd5e1;

        /* 텍스트 색상 */
        --text: #1e293b;
        --text-secondary: #475569;
        --text-muted: #64748b;

        /* Neumorphism 그림자 */
        --shadow-light: rgba(255, 255, 255, 0.7);
        --shadow-dark: rgba(148, 163, 184, 0.4);
        --shadow-inset-light: rgba(255, 255, 255, 0.9);
        --shadow-inset-dark: rgba(148, 163, 184, 0.3);

        /* 기본 설정 */
        --border-radius: 20px;
        --border-radius-large: 30px;
        --border-radius-small: 12px;
    }

    /* Streamlit 전체 배경 */
    .stApp {
        background: linear-gradient(135deg, #e0e7ff 0%, #f1f5f9 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* 메인 컨테이너 */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }

    /* Neumorphism 카드 기본 스타일 */
    .neumorphism-card {
        background: var(--surface);
        border-radius: var(--border-radius);
        box-shadow:
                12px 12px 24px var(--shadow-dark),
                -12px -12px 24px var(--shadow-light);
        transition: all 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 2rem;
        margin: 1rem 0;
    }

    .neumorphism-card:hover {
        transform: translateY(-2px);
        box-shadow:
                16px 16px 32px var(--shadow-dark),
                -16px -16px 32px var(--shadow-light);
    }

    /* 헤더 스타일 */
    .main-header {
        background: var(--surface);
        border-radius: var(--border-radius-large);
        padding: 40px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow:
                20px 20px 40px var(--shadow-dark),
                -20px -20px 40px var(--shadow-light);
    }

    .main-header h1 {
        font-size: 3.5em;
        font-weight: 700;
        color: var(--text);
        margin-bottom: 15px;
        letter-spacing: -0.02em;
        text-shadow: 2px 2px 4px rgba(148, 163, 184, 0.3);
    }

    .main-header p {
        font-size: 1.4em;
        font-weight: 400;
        color: var(--text-secondary);
        margin: 0;
    }

    .white-bg-black-text {
        background: linear-gradient(145deg, #ffffff, #f8fafc);
        color: var(--text);
        padding: 4px 8px;
        border-radius: 12px;
        font-weight: 900;
        box-shadow:
                2px 2px 4px var(--shadow-dark),
                -2px -2px 4px var(--shadow-light);
    }

    /* 통계 카드 */
    .stat-card {
        background: var(--surface);
        padding: 20px 25px;
        border-radius: var(--border-radius);
        text-align: center;
        min-width: 120px;
        box-shadow:
                8px 8px 16px var(--shadow-dark),
                -8px -8px 16px var(--shadow-light);
        transition: all 0.3s ease;
        margin: 0.5rem;
    }

    .stat-card:hover {
        transform: translateY(-1px);
        box-shadow:
                10px 10px 20px var(--shadow-dark),
                -10px -10px 20px var(--shadow-light);
    }

    .stat-number {
        font-size: 2.2em;
        font-weight: 700;
        color: var(--accent);
        display: block;
        text-shadow: 1px 1px 2px rgba(139, 92, 246, 0.3);
    }

    .stat-label {
        font-size: 1em;
        color: var(--text-muted);
        margin-top: 5px;
    }

    /* 서비스 카드 */
    .service-card {
        background: var(--surface);
        border-radius: var(--border-radius);
        padding: 25px;
        margin: 1rem 0;
        box-shadow:
                12px 12px 24px var(--shadow-dark),
                -12px -12px 24px var(--shadow-light);
        transition: all 0.3s ease;
    }

    .service-card:hover {
        transform: translateY(-1px);
        box-shadow:
                16px 16px 32px var(--shadow-dark),
                -16px -16px 32px var(--shadow-light);
    }

    .service-card h3 {
        color: var(--text);
        margin: 0;
        text-shadow: 1px 1px 2px rgba(148, 163, 184, 0.3);
    }

    .openai-card {
        background: linear-gradient(145deg, #d1fae5, #ecfdf5);
        border: 1px solid rgba(16, 185, 129, 0.2);
    }

    .openai-card h3 {
        color: var(--openai-dark);
    }

    /* 결과 카드 */
    .result-card {
        background: var(--surface);
        border-radius: var(--border-radius);
        padding: 25px;
        margin: 20px 0;
        transition: all 0.3s ease;
        box-shadow:
                8px 8px 16px var(--shadow-dark),
                -8px -8px 16px var(--shadow-light);
    }

    .result-card:hover {
        transform: translateY(-1px);
        box-shadow:
                12px 12px 24px var(--shadow-dark),
                -12px -12px 24px var(--shadow-light);
    }

    .result-card h4 {
        color: var(--text);
        margin-bottom: 15px;
        text-shadow: 1px 1px 2px rgba(148, 163, 184, 0.2);
    }

    .error-card {
        background: linear-gradient(145deg, #fecaca, #fee2e2);
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    .error-card h4, .error-card p {
        color: var(--error);
    }

    /* Streamlit 컴포넌트 커스터마이징 */
    .stTextArea > div > div > textarea {
        background: var(--surface);
        border: none;
        border-radius: var(--border-radius);
        color: var(--text);
        font-size: 17px;
        font-family: 'Inter', sans-serif;
        box-shadow:
                inset 8px 8px 16px var(--shadow-inset-dark),
                inset -8px -8px 16px var(--shadow-inset-light);
        transition: all 0.3s ease;
    }

    .stTextArea > div > div > textarea:focus {
        box-shadow:
                inset 10px 10px 20px var(--shadow-inset-dark),
                inset -10px -10px 20px var(--shadow-inset-light),
                0 0 0 3px rgba(79, 70, 229, 0.1);
    }

    /* 선택박스 스타일링 */
    .stSelectbox > div > div {
        background: var(--surface);
        border: none;
        border-radius: var(--border-radius-small);
        box-shadow:
                inset 6px 6px 12px var(--shadow-inset-dark),
                inset -6px -6px 12px var(--shadow-inset-light);
    }

    /* 체크박스 스타일링 */
    .stCheckbox > label {
        background: var(--surface);
        border-radius: var(--border-radius-small);
        padding: 10px;
        box-shadow:
                6px 6px 12px var(--shadow-dark),
                -6px -6px 12px var(--shadow-light);
        transition: all 0.3s ease;
    }

    .stCheckbox > label:hover {
        transform: translateY(-1px);
        box-shadow:
                8px 8px 16px var(--shadow-dark),
                -8px -8px 16px var(--shadow-light);
    }

    /* 슬라이더 스타일링 */
    .stSlider > div > div > div {
        background: var(--surface);
        box-shadow:
                inset 3px 3px 6px var(--shadow-inset-dark),
                inset -3px -3px 6px var(--shadow-inset-light);
    }

    /* 버튼 스타일링 */
    .stButton > button {
        background: linear-gradient(145deg, #4f46e5, #6366f1);
        border: none;
        border-radius: var(--border-radius);
        color: white;
        font-weight: 600;
        padding: 18px;
        font-size: 1.3em;
        box-shadow:
                12px 12px 24px var(--shadow-dark),
                -12px -12px 24px var(--shadow-light);
        transition: all 0.3s ease;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow:
                16px 16px 32px var(--shadow-dark),
                -16px -16px 32px var(--shadow-light);
    }

    .stButton > button:active {
        transform: translateY(0px);
        box-shadow:
                inset 6px 6px 12px rgba(79, 70, 229, 0.3),
                inset -6px -6px 12px rgba(255, 255, 255, 0.1);
    }

    /* 다운로드 버튼 */
    .stDownloadButton > button {
        background: linear-gradient(145deg, #22c55e, #16a34a);
        border: none;
        border-radius: var(--border-radius-small);
        color: white;
        font-weight: 500;
        padding: 14px 22px;
        box-shadow:
                6px 6px 12px var(--shadow-dark),
                -6px -6px 12px var(--shadow-light);
        transition: all 0.3s ease;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
    }

    .stDownloadButton > button:hover {
        transform: translateY(-1px);
        box-shadow:
                8px 8px 16px var(--shadow-dark),
                -8px -8px 16px var(--shadow-light);
    }

    /* 사이드바 스타일링 */
    .css-1d391kg {
        background: var(--surface);
        box-shadow:
                12px 12px 24px var(--shadow-dark),
                -12px -12px 24px var(--shadow-light);
        border-radius: var(--border-radius);
    }

    /* 오디오 플레이어 */
    audio {
        width: 100%;
        border-radius: var(--border-radius);
        box-shadow:
                4px 4px 8px var(--shadow-dark),
                -4px -4px 8px var(--shadow-light);
        margin: 15px 0;
    }

    /* 성공/에러 메시지 */
    .stSuccess {
        background: linear-gradient(145deg, #dcfce7, #f0fdf4);
        border: 1px solid var(--success);
        border-radius: var(--border-radius);
        box-shadow:
                6px 6px 12px var(--shadow-dark),
                -6px -6px 12px var(--shadow-light);
    }

    .stError {
        background: linear-gradient(145deg, #fecaca, #fee2e2);
        border: 1px solid var(--error);
        border-radius: var(--border-radius);
        box-shadow:
                6px 6px 12px var(--shadow-dark),
                -6px -6px 12px var(--shadow-light);
    }

    .stWarning {
        background: linear-gradient(145deg, #fef3c7, #fffbeb);
        border: 1px solid var(--warning);
        border-radius: var(--border-radius);
        box-shadow:
                6px 6px 12px var(--shadow-dark),
                -6px -6px 12px var(--shadow-light);
    }

    .stInfo {
        background: linear-gradient(145deg, #dbeafe, #eff6ff);
        border: 1px solid var(--primary);
        border-radius: var(--border-radius);
        box-shadow:
                6px 6px 12px var(--shadow-dark),
                -6px -6px 12px var(--shadow-light);
    }

    /* Expander 스타일링 */
    .streamlit-expanderHeader {
        background: var(--surface);
        border-radius: var(--border-radius);
        box-shadow:
                8px 8px 16px var(--shadow-dark),
                -8px -8px 16px var(--shadow-light);
        transition: all 0.3s ease;
    }

    .streamlit-expanderHeader:hover {
        transform: translateY(-1px);
        box-shadow:
                12px 12px 24px var(--shadow-dark),
                -12px -12px 24px var(--shadow-light);
    }

    /* 스피너 */
    .stSpinner > div {
        border-color: var(--accent);
    }

    /* 서비스 태그 */
    .service-tag {
        background: linear-gradient(145deg, #8b5cf6, #a78bfa);
        color: white;
        padding: 10px 18px;
        border-radius: 20px;
        font-size: 1em;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 15px;
        box-shadow:
                4px 4px 8px rgba(139, 92, 246, 0.3),
                -2px -2px 4px rgba(255, 255, 255, 0.1);
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
    }

    .service-tag.openai-tag {
        background: linear-gradient(145deg, #10b981, #34d399);
        box-shadow:
                4px 4px 8px rgba(16, 185, 129, 0.3),
                -2px -2px 4px rgba(255, 255, 255, 0.1);
    }

    /* 서비스 그룹 카운트 */
    .service-group-count {
        background: linear-gradient(145deg, #8b5cf6, #a78bfa);
        color: white;
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.85em;
        font-weight: 500;
        margin-left: auto;
        box-shadow:
                3px 3px 6px rgba(139, 92, 246, 0.3),
                -1px -1px 2px rgba(255, 255, 255, 0.1);
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
    }

    .service-group-count.openai-count {
        background: linear-gradient(145deg, #10b981, #34d399);
        box-shadow:
                3px 3px 6px rgba(16, 185, 129, 0.3),
                -1px -1px 2px rgba(255, 255, 255, 0.1);
    }

    /* 서비스 아이콘 */
    .service-icon {
        font-size: 1.4em;
        color: var(--accent-light);
        text-shadow: 1px 1px 2px rgba(167, 139, 250, 0.3);
    }

    .openai-icon {
        color: var(--openai) !important;
        text-shadow: 1px 1px 2px rgba(16, 185, 129, 0.3);
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }

    @keyframes softPulse {
        0%, 100% {
            box-shadow:
                    12px 12px 24px var(--shadow-dark),
                    -12px -12px 24px var(--shadow-light);
        }
        50% {
            box-shadow:
                    16px 16px 32px var(--shadow-dark),
                    -16px -16px 32px var(--shadow-light);
        }
    }

    .stButton > button:not(:disabled):not(:active) {
        animation: softPulse 3s ease-in-out infinite;
    }

    /* 반응형 디자인 */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2.8em;
        }
        
        .main-header p {
            font-size: 1.2em;
        }
        
        .stat-card {
            margin: 0.2rem;
            min-width: 100px;
        }
        
        .stat-number {
            font-size: 1.8em;
        }
    }
</style>
""", unsafe_allow_html=True)

# 메인 헤더 (원본 HTML 스타일 완전 재현)
st.markdown("""
<div class="main-header neumorphism-card">
    <h1><i class="fas fa-microphone-alt"></i> <span class="white-bg-black-text">SWING</span> AI Voice Studio</h1>
    <p>더스윙 AI 음성 생성 스튜디오 + OpenAI TTS 🚀</p>
    <div style="display: flex; justify-content: center; gap: 30px; flex-wrap: wrap; margin-top: 20px;">
        <div class="stat-card">
            <span class="stat-number">{}</span>
            <div class="stat-label">생성된 음성</div>
        </div>
        <div class="stat-card">
            <span class="stat-number">15</span>
            <div class="stat-label">음성 옵션</div>
        </div>
        <div class="stat-card">
            <span class="stat-number">∞</span>
            <div class="stat-label">가능성</div>
        </div>
    </div>
</div>
""".format(st.session_state.total_generated), unsafe_allow_html=True)

# FontAwesome 아이콘 추가
st.markdown("""
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
""", unsafe_allow_html=True)

# 사이드바 설정
with st.sidebar:
    st.header("🔧 AI 서비스 설정")

    # API 키 설정
    st.subheader("🔑 API Keys")
    if not ELEVENLABS_API_KEY:
        st.warning("ElevenLabs API 키를 설정하세요")
        elevenlabs_key = st.text_input("ElevenLabs API Key", type="password", help="고급 AI 음성을 위해 필요")
    else:
        st.success("✅ ElevenLabs API 연결됨")
        elevenlabs_key = ELEVENLABS_API_KEY

    if not OPENAI_API_KEY:
        st.warning("OpenAI API 키를 설정하세요")
        openai_key = st.text_input("OpenAI API Key", type="password", help="최신 GPT 음성을 위해 필요")
    else:
        st.success("✅ OpenAI API 연결됨")
        openai_key = OPENAI_API_KEY

    st.divider()

    # 서비스 선택
    st.subheader("🤖 AI 서비스 선택")
    use_google = st.checkbox("🌟 Google TTS", value=True, help="무료 • 다국어 지원")
    use_elevenlabs = st.checkbox("🧠 ElevenLabs", help="프리미엄 • AI 음성")
    use_openai = st.checkbox("🚀 OpenAI TTS", help="GPT • 초고품질")

    st.divider()

    # 생성 개수
    generation_count = st.selectbox(
        "📊 생성 개수",
        options=[1, 2, 3, 4, 5, 6, 10],
        index=2,
        help="각 서비스별로 생성할 음성 개수"
    )

# 메인 컨텐츠
st.header(":primary[✍️ 텍스트 입력]")

text_input = st.text_area(
    ":primary[변환할 텍스트를 입력하세요:]",
    height=150,
    max_chars=4096,
    help="최대 4096자까지 입력 가능합니다"
)

# 문자 수 표시
if text_input:
    char_count = len(text_input)
    if char_count > 3500:
        st.warning(f":primary[⚠️ {char_count}/4096 characters - 거의 한계에 도달했습니다]")
    else:
        st.info(f":primary[📝 {char_count}/4096 characters]")

# 서비스별 설정
col1, col2, col3 = st.columns(3)

# Google TTS 설정
if use_google:
    with col1:
        with st.expander(":primary[🌟 Google TTS 설정]", expanded=True):
            google_lang = st.selectbox(
                ":primary[언어]",
                options=[lang["code"] for lang in tts_generator.google_languages],
                format_func=lambda x: next(lang["name"] for lang in tts_generator.google_languages if lang["code"] == x),
                index=0
            )
            google_slow = st.checkbox(":primary[느린 속도]", help=":primary[언어 학습에 유용]")

# ElevenLabs 설정
if use_elevenlabs:
    with col2:
        with st.expander("🧠 ElevenLabs 설정", expanded=True):
            if elevenlabs_key:
                voice_options = {f"{voice['name']} ({voice['gender']})": voice['id'] for voice in tts_generator.elevenlabs_voices}
                selected_voice = st.selectbox("음성 캐릭터", options=list(voice_options.keys()))
                voice_id = voice_options[selected_voice]

                model_options = {model['name']: model['id'] for model in tts_generator.elevenlabs_models}
                selected_model = st.selectbox("AI 모델", options=list(model_options.keys()), index=2)
                model_id = model_options[selected_model]

                stability = st.slider("Stability (안정성)", 0.0, 1.0, 0.5, 0.1, help="낮음=더 표현력, 높음=더 안정적")
                similarity = st.slider("Similarity (유사성)", 0.0, 1.0, 0.5, 0.1, help="원본 음성 특성 유지 정도")
                style = st.slider("Style (감정 표현)", 0.0, 1.0, 0.0, 0.1, help="0=자연스럽게, 1=극도로 감정적")
                speaker_boost = st.checkbox("Speaker Boost", value=True, help="음성 품질 향상")
            else:
                st.warning("API 키를 입력해주세요")

# OpenAI TTS 설정
if use_openai:
    with col3:
        with st.expander("🚀 OpenAI TTS 설정", expanded=True):
            if openai_key:
                voice_options = {f"{voice['name']} - {voice['description']}": voice['id'] for voice in tts_generator.openai_voices}
                selected_openai_voice = st.selectbox("AI 음성", options=list(voice_options.keys()))
                openai_voice_id = voice_options[selected_openai_voice]

                model_options = {model['name']: model['id'] for model in tts_generator.openai_models}
                selected_openai_model = st.selectbox("AI 모델", options=list(model_options.keys()))
                openai_model_id = model_options[selected_openai_model]

                openai_speed = st.slider("음성 속도", 0.25, 4.0, 1.0, 0.25, help="0.25x=매우 느림, 1.0x=보통, 4.0x=매우 빠름")

                format_options = {format_item['name']: format_item['id'] for format_item in tts_generator.openai_formats}
                selected_format = st.selectbox("오디오 포맷", options=list(format_options.keys()))
                audio_format = format_options[selected_format]
            else:
                st.warning("API 키를 입력해주세요")

# 생성 버튼
st.divider()
if st.button("🎵 AI 음성 생성하기", type="primary", use_container_width=True):
    if not text_input.strip():
        st.error("⚠️ 텍스트를 입력해주세요!")
    elif not (use_google or use_elevenlabs or use_openai):
        st.error("⚠️ AI 서비스를 하나 이상 선택해주세요!")
    elif len(text_input) > 4096:
        st.error("⚠️ 텍스트가 너무 깁니다. 4096자 이하로 입력해주세요")
    else:
        # 음성 생성 프로세스
        with st.spinner("🎤 AI 음성 생성 중..."):
            results = []

            # Google TTS 생성
            if use_google:
                google_settings = {
                    'language': google_lang,
                    'slow': google_slow
                }
                result = tts_generator.generate_google_tts(text_input, google_settings)
                results.append(result)

            # ElevenLabs TTS 생성 (여러 개)
            if use_elevenlabs and elevenlabs_key:
                for i in range(generation_count):
                    # 여러 개 생성시 다른 음성 사용
                    current_voice_id = voice_id
                    if generation_count > 1:
                        voice_index = i % len(tts_generator.elevenlabs_voices)
                        current_voice_id = tts_generator.elevenlabs_voices[voice_index]['id']

                    elevenlabs_settings = {
                        'voice_id': current_voice_id,
                        'model_id': model_id,
                        'stability': stability,
                        'similarity_boost': similarity,
                        'style': style,
                        'use_speaker_boost': speaker_boost
                    }
                    result = tts_generator.generate_elevenlabs_tts(text_input, elevenlabs_settings)
                    results.append(result)

            # OpenAI TTS 생성 (여러 개)
            if use_openai and openai_key:
                for i in range(generation_count):
                    # 여러 개 생성시 다른 음성 사용
                    current_voice_id = openai_voice_id
                    if generation_count > 1:
                        voice_index = i % len(tts_generator.openai_voices)
                        current_voice_id = tts_generator.openai_voices[voice_index]['id']

                    openai_settings = {
                        'voice': current_voice_id,
                        'model': openai_model_id,
                        'speed': openai_speed,
                        'response_format': audio_format
                    }
                    result = tts_generator.generate_openai_tts(text_input, openai_settings)
                    results.append(result)

        # 결과 처리
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]

        if successful_results:
            st.success(f"🎉 {len(successful_results)}개의 AI 음성이 성공적으로 생성되었습니다!")

            # 세션 상태 업데이트
            st.session_state.generated_audios.extend(successful_results)
            st.session_state.total_generated += len(successful_results)

            # 결과 표시
            st.header("🎧 생성된 음성 파일들")

            # 서비스별로 그룹핑
            google_results = [r for r in successful_results if 'Google' in r['service']]
            elevenlabs_results = [r for r in successful_results if 'ElevenLabs' in r['service']]
            openai_results = [r for r in successful_results if 'OpenAI' in r['service']]

            # Google TTS 결과
            if google_results:
                st.markdown("""
                <div class="service-card">
                    <h3><i class="fab fa-google"></i> Google TTS <span style="background: linear-gradient(145deg, #8b5cf6, #a78bfa); color: white; padding: 4px 12px; border-radius: 15px; font-size: 0.85em; font-weight: 500; margin-left: 10px; box-shadow: 3px 3px 6px rgba(139, 92, 246, 0.3), -1px -1px 2px rgba(255, 255, 255, 0.1); text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);">{}/{}</span></h3>
                </div>
                """.format(len(google_results), len(google_results)), unsafe_allow_html=True)

                for i, result in enumerate(google_results):
                    with st.container():
                        st.markdown(f"""
                        <div class="result-card fade-in">
                            <div style="margin-bottom: 20px;">
                                <span style="background: linear-gradient(145deg, #8b5cf6, #a78bfa); color: white; padding: 10px 18px; border-radius: 20px; font-size: 1em; font-weight: 600; display: inline-flex; align-items: center; gap: 8px; margin-bottom: 15px; box-shadow: 4px 4px 8px rgba(139, 92, 246, 0.3), -2px -2px 4px rgba(255, 255, 255, 0.1); text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);">
                                    <i class="fab fa-google"></i>
                                    {result['service']}
                                </span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # 오디오 플레이어
                        st.audio(result['audio_data'], format='audio/mp3')

                        # 다운로드 버튼
                        st.download_button(
                            "📥 다운로드",
                            data=result['audio_data'],
                            file_name=result['filename'],
                            mime="audio/mp3",
                            key=f"google_download_{i}"
                        )

            # ElevenLabs 결과
            if elevenlabs_results:
                st.markdown("""
                <div class="service-card">
                    <h3><i class="fas fa-brain"></i> ElevenLabs AI <span style="background: linear-gradient(145deg, #8b5cf6, #a78bfa); color: white; padding: 4px 12px; border-radius: 15px; font-size: 0.85em; font-weight: 500; margin-left: 10px; box-shadow: 3px 3px 6px rgba(139, 92, 246, 0.3), -1px -1px 2px rgba(255, 255, 255, 0.1); text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);">{}/{}</span></h3>
                </div>
                """.format(len(elevenlabs_results), len(elevenlabs_results)), unsafe_allow_html=True)

                for i, result in enumerate(elevenlabs_results):
                    with st.container():
                        st.markdown(f"""
                        <div class="result-card fade-in">
                            <div style="margin-bottom: 20px;">
                                <span style="background: linear-gradient(145deg, #8b5cf6, #a78bfa); color: white; padding: 10px 18px; border-radius: 20px; font-size: 1em; font-weight: 600; display: inline-flex; align-items: center; gap: 8px; margin-bottom: 15px; box-shadow: 4px 4px 8px rgba(139, 92, 246, 0.3), -2px -2px 4px rgba(255, 255, 255, 0.1); text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);">
                                    <i class="fas fa-brain"></i>
                                    {result['service']}
                                </span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # 오디오 플레이어
                        st.audio(result['audio_data'], format='audio/mp3')

                        # 다운로드 버튼
                        st.download_button(
                            "📥 다운로드",
                            data=result['audio_data'],
                            file_name=result['filename'],
                            mime="audio/mp3",
                            key=f"elevenlabs_download_{i}"
                        )

            # OpenAI 결과
            if openai_results:
                st.markdown("""
                <div class="service-card openai-card">
                    <h3><i class="fas fa-robot" style="color: var(--openai);"></i> OpenAI TTS 🚀 <span style="background: linear-gradient(145deg, #10b981, #34d399); color: white; padding: 4px 12px; border-radius: 15px; font-size: 0.85em; font-weight: 500; margin-left: 10px; box-shadow: 3px 3px 6px rgba(16, 185, 129, 0.3), -1px -1px 2px rgba(255, 255, 255, 0.1); text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);">{}/{}</span></h3>
                </div>
                """.format(len(openai_results), len(openai_results)), unsafe_allow_html=True)

                for i, result in enumerate(openai_results):
                    with st.container():
                        st.markdown(f"""
                        <div class="result-card fade-in">
                            <div style="margin-bottom: 20px;">
                                <span style="background: linear-gradient(145deg, #10b981, #34d399); color: white; padding: 10px 18px; border-radius: 20px; font-size: 1em; font-weight: 600; display: inline-flex; align-items: center; gap: 8px; margin-bottom: 15px; box-shadow: 4px 4px 8px rgba(16, 185, 129, 0.3), -2px -2px 4px rgba(255, 255, 255, 0.1); text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);">
                                    <i class="fas fa-robot"></i>
                                    {result['service']}
                                </span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # 오디오 플레이어 (포맷에 따라)
                        audio_format = result.get('settings', {}).get('response_format', 'mp3')
                        if audio_format == 'mp3':
                            st.audio(result['audio_data'], format='audio/mp3')
                        elif audio_format == 'ogg' or audio_format == 'opus':
                            st.audio(result['audio_data'], format='audio/ogg')
                        else:
                            st.audio(result['audio_data'])

                        # 다운로드 버튼
                        st.download_button(
                            "📥 다운로드",
                            data=result['audio_data'],
                            file_name=result['filename'],
                            mime=f"audio/{audio_format}",
                            key=f"openai_download_{i}"
                        )

        # 실패한 결과 표시 (원본 스타일 적용)
        if failed_results:
            st.markdown('<h3 style="color: var(--text); text-align: center; margin: 2rem 0;"><i class="fas fa-exclamation-triangle"></i> 생성 실패</h3>', unsafe_allow_html=True)
            for result in failed_results:
                st.markdown(f"""
                <div class="result-card error-card fade-in">
                    <div style="display: flex; align-items: center; gap: 12px; font-weight: 500;">
                        <i class="fas fa-exclamation-triangle"></i>
                        <strong>{result['service']}</strong> 생성 실패: {result['error']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

# 히스토리 표시
if st.session_state.generated_audios:
    st.divider()
    with st.expander(f"📜 생성 히스토리 ({len(st.session_state.generated_audios)}개)", expanded=False):
        for i, audio in enumerate(reversed(st.session_state.generated_audios[-10:])):  # 최근 10개만
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"🎵 {audio['service']}")
                st.audio(audio['audio_data'])
            with col2:
                st.download_button(
                    "📥",
                    data=audio['audio_data'],
                    file_name=audio['filename'],
                    mime="audio/mp3",
                    key=f"history_download_{i}"
                )

# 정리 버튼
if st.session_state.generated_audios:
    if st.button("🗑️ 히스토리 모두 지우기", type="secondary"):
        st.session_state.generated_audios = []
        st.success("✅ 히스토리가 모두 지워졌습니다!")
        st.rerun()