import os
import tempfile
import requests
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.http import HttpResponse
from TTS.api import TTS

MODEL_URL = "https://www.dropbox.com/scl/fi/rl6ls4vnxe0517ampy9v8/model.pth?rlkey=0cdji2tjze3fzmugwel3gl50d&st=vbaczw04&dl=0"
CONFIG_PATH = os.path.join(settings.BASE_DIR, "clone", "models", "xtts_v2", "config.json")

def download_model(url, save_path):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def clone_voice(original_audio_path, text):
    model_dir = os.path.join(settings.BASE_DIR, "clone", "models", "xtts_v2")
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)

    model_path = os.path.join(model_dir)
    if not os.path.exists(model_path):
        download_model(MODEL_URL, model_path)

    tts = TTS(model_path=model_path, config_path=CONFIG_PATH)
    
    temp_output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tts.tts_to_file(text=text, file_path=temp_output_file.name, speaker_wav=original_audio_path, language="en")
    return temp_output_file.name

def index(request):
    if request.method == 'POST' and request.FILES['audio'] and 'text' in request.POST:
        audio_file = request.FILES['audio']
        text = request.POST['text']

        fs = FileSystemStorage()
        filename = fs.save(audio_file.name, audio_file)
        uploaded_file_url = fs.path(filename)

        generated_audio_path = clone_voice(uploaded_file_url, text)

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'generated'))
        generated_audio_filename = fs.save(os.path.basename(generated_audio_path), open(generated_audio_path, 'rb'))
        generated_audio_url = fs.url(os.path.join('generated', generated_audio_filename))

        os.remove(uploaded_file_url)
        os.remove(generated_audio_path)

        return render(request, 'clone/index.html', {
            'generated_audio_url': generated_audio_url
        })

    return render(request, 'clone/index.html')
