from flask import Flask, render_template, request, jsonify, send_file
import os
import uuid
import requests
from gtts import gTTS
import tempfile
import json

app = Flask(__name__)

# 설정
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# 출력 폴더 생성
UPLOAD_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

        # 🚀 OpenAI TTS 음성 목록 (NEW!)
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
            {"code": "ko", "name": "한국어"},
            {"code": "en", "name": "English"},
            {"code": "ja", "name": "日本語"},
            {"code": "zh", "name": "中文"},
            {"code": "es", "name": "Español"},
            {"code": "fr", "name": "Français"},
            {"code": "de", "name": "Deutsch"},
            {"code": "it", "name": "Italiano"},
            {"code": "pt", "name": "Português"},
            {"code": "ru", "name": "Русский"}
        ]

        # 임시 파일 저장용
        self.temp_files = {}

    def generate_google_tts(self, text, settings):
        """구글 TTS로 음성 생성"""
        try:
            lang = settings.get('language', 'ko')
            slow = settings.get('slow', False)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            tts = gTTS(text=text, lang=lang, slow=slow)
            tts.save(temp_file.name)

            file_id = str(uuid.uuid4())
            self.temp_files[file_id] = {
                'path': temp_file.name,
                'service': f'Google TTS ({lang.upper()})'
            }

            return {
                "success": True,
                "file_id": file_id,
                "service": f"Google TTS ({lang.upper()})",
                "settings": settings
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
            voice_id = settings.get('voice_id', self.elevenlabs_voices[0]["id"])
            model_id = settings.get('model_id', 'eleven_monolingual_v1')
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
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                temp_file.write(response.content)
                temp_file.close()

                voice_name = next((v["name"] for v in self.elevenlabs_voices if v["id"] == voice_id), "Unknown")
                model_name = next((m["name"] for m in self.elevenlabs_models if m["id"] == model_id), "Unknown")

                file_id = str(uuid.uuid4())
                self.temp_files[file_id] = {
                    'path': temp_file.name,
                    'service': f'ElevenLabs ({voice_name} - {model_name})'
                }

                return {
                    "success": True,
                    "file_id": file_id,
                    "service": f"ElevenLabs ({voice_name} - {model_name})",
                    "settings": settings
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
        """🚀 OpenAI TTS로 음성 생성 (NEW!)"""
        try:
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
                file_extension = audio_format if audio_format != 'opus' else 'ogg'
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}')
                temp_file.write(response.content)
                temp_file.close()

                voice_name = next((v["name"] for v in self.openai_voices if v["id"] == voice), voice)
                model_name = next((m["name"] for m in self.openai_models if m["id"] == model), model)

                file_id = str(uuid.uuid4())
                self.temp_files[file_id] = {
                    'path': temp_file.name,
                    'service': f'OpenAI TTS ({voice_name} - {model_name})'
                }

                return {
                    "success": True,
                    "file_id": file_id,
                    "service": f"OpenAI TTS ({voice_name} - {model_name})",
                    "settings": settings
                }
            else:
                error_msg = f"OpenAI API Error: {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg += f" - {error_data['error'].get('message', 'Unknown error')}"
                except:
                    pass

                if response.status_code == 401:
                    error_msg += " - API 키를 확인해주세요"
                elif response.status_code == 429:
                    error_msg += " - 사용량 한도를 초과했습니다"
                elif response.status_code == 400:
                    error_msg += " - 잘못된 요청 형식입니다"

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

    def get_elevenlabs_voices(self):
        """실제 일레븐랩스 API에서 음성 목록 가져오기"""
        try:
            url = "https://api.elevenlabs.io/v1/voices"
            headers = {"xi-api-key": ELEVENLABS_API_KEY}
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                voices_data = response.json()
                return voices_data.get("voices", self.elevenlabs_voices)
            else:
                return self.elevenlabs_voices
        except:
            return self.elevenlabs_voices

# TTS 생성기 인스턴스
tts_generator = TTSGenerator()

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_audio():
    """음성 생성 API"""
    try:
        data = request.json
        print("받은 데이터:", data)

        text = data.get('text', '').strip()
        count = int(data.get('count', 1))
        services = data.get('services', [])
        settings = data.get('settings', {})

        # 입력 검증
        if not text:
            return jsonify({"error": "텍스트를 입력해주세요!"}), 400

        if not services:
            return jsonify({"error": "TTS 서비스를 선택해주세요!"}), 400

        if len(text) > 4096:  # OpenAI TTS 텍스트 길이 제한
            return jsonify({"error": "텍스트가 너무 깁니다. (최대 4096자)"}), 400

        results = []

        # Google TTS 처리
        if 'google' in services:
            google_settings = settings.get('google', {})
            result = tts_generator.generate_google_tts(text, google_settings)
            results.append(result)

        # ElevenLabs 처리
        if 'elevenlabs' in services:
            elevenlabs_settings = settings.get('elevenlabs', {})
            elevenlabs_count = elevenlabs_settings.get('count', 1)

            for i in range(elevenlabs_count):
                # 여러 개 생성 시 다른 음성 사용
                if elevenlabs_count > 1 and not elevenlabs_settings.get('voice_id'):
                    voice_index = i % len(tts_generator.elevenlabs_voices)
                    elevenlabs_settings['voice_id'] = tts_generator.elevenlabs_voices[voice_index]['id']

                result = tts_generator.generate_elevenlabs_tts(text, elevenlabs_settings)
                results.append(result)

        # 🚀 OpenAI TTS 처리 (NEW!)
        if 'openai' in services:
            openai_settings = settings.get('openai', {})
            openai_count = openai_settings.get('count', 1)

            for i in range(openai_count):
                # 여러 개 생성 시 다른 음성 사용
                if openai_count > 1 and not openai_settings.get('voice'):
                    voice_index = i % len(tts_generator.openai_voices)
                    openai_settings['voice'] = tts_generator.openai_voices[voice_index]['id']

                result = tts_generator.generate_openai_tts(text, openai_settings)
                results.append(result)

        return jsonify({"results": results})

    except Exception as e:
        print(f"Error in generate_audio: {str(e)}")
        return jsonify({"error": f"서버 오류: {str(e)}"}), 500

@app.route('/play/<file_id>')
def play_file(file_id):
    """음성 파일 재생"""
    try:
        if file_id in tts_generator.temp_files:
            file_path = tts_generator.temp_files[file_id]['path']
            if os.path.exists(file_path):
                # 파일 확장자에 따라 MIME 타입 설정
                if file_path.endswith('.mp3'):
                    mimetype = 'audio/mpeg'
                elif file_path.endswith('.ogg'):
                    mimetype = 'audio/ogg'
                elif file_path.endswith('.aac'):
                    mimetype = 'audio/aac'
                elif file_path.endswith('.flac'):
                    mimetype = 'audio/flac'
                else:
                    mimetype = 'audio/mpeg'

                return send_file(file_path, mimetype=mimetype)
            else:
                return "파일이 존재하지 않습니다.", 404
        else:
            return "파일을 찾을 수 없습니다.", 404
    except Exception as e:
        print(f"Error in play_file: {str(e)}")
        return f"파일 재생 오류: {str(e)}", 500

@app.route('/download/<file_id>')
def download_file(file_id):
    """음성 파일 다운로드"""
    try:
        if file_id in tts_generator.temp_files:
            file_path = tts_generator.temp_files[file_id]['path']
            if os.path.exists(file_path):
                service_name = tts_generator.temp_files[file_id]['service'].replace(' ', '_').replace('(', '').replace(')', '')
                file_extension = os.path.splitext(file_path)[1]
                download_name = f'{service_name}_{file_id[:8]}{file_extension}'
                return send_file(file_path, as_attachment=True, download_name=download_name)
            else:
                return "파일이 존재하지 않습니다.", 404
        else:
            return "파일을 찾을 수 없습니다.", 404
    except Exception as e:
        print(f"Error in download_file: {str(e)}")
        return f"파일 다운로드 오류: {str(e)}", 500

@app.route('/api/voices')
def get_voices():
    """모든 서비스의 음성 목록 API"""
    try:
        return jsonify({
            "elevenlabs_voices": tts_generator.get_elevenlabs_voices(),
            "google_languages": tts_generator.google_languages,
            "openai_voices": tts_generator.openai_voices,  # 🚀 NEW!
            "openai_models": tts_generator.openai_models,  # 🚀 NEW!
            "openai_formats": tts_generator.openai_formats  # 🚀 NEW!
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    """생성된 파일들 정리"""
    try:
        cleaned_count = 0
        for file_id, file_info in list(tts_generator.temp_files.items()):
            try:
                if os.path.exists(file_info['path']):
                    os.remove(file_info['path'])
                    cleaned_count += 1
                del tts_generator.temp_files[file_id]
            except Exception as e:
                print(f"파일 삭제 실패: {e}")

        return jsonify({"message": f"{cleaned_count}개 파일이 정리되었습니다."})
    except Exception as e:
        return jsonify({"error": f"파일 정리 실패: {str(e)}"}), 500

# 에러 핸들러
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "페이지를 찾을 수 없습니다."}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "서버 내부 오류가 발생했습니다."}), 500

if __name__ == '__main__':
    print("🎤 Advanced TTS 웹서버 시작!")
    print("📱 브라우저에서 http://127.0.0.1:5000 접속하세요!")
    print("🔧 ElevenLabs API 키를 설정하면 고급 기능을 사용할 수 있습니다.")
    print("🚀 OpenAI API 키를 설정하면 최신 GPT 음성을 사용할 수 있습니다!")
    print("🎛️  각 서비스별 세부 설정을 조정해보세요!")
    print(f"📁 Templates 폴더: {app.template_folder}")
    print("=" * 60)

    app.run(debug=True, host='localhost', port=5000)