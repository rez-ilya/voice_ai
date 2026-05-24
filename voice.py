import os
import json
import pyaudio
import pyttsx3
from vosk import Model, KaldiRecognizer

# https://github.com/trashchenkov/gigachat_tutorials тут есть SaluteSpeech API + GigaChat API

# Настройки
MODEL_PATH = "vosk-model-small-ru"
if not os.path.exists(MODEL_PATH):
    print("Ошибка: Папка с моделью Vosk не найдена!")
    exit(1)

model = Model(MODEL_PATH)


def speak(text: str):
    """Функция озвучки: создает движок, говорит и полностью закрывается"""
    print(f"Ассистент: {text}")
    engine = pyttsx3.init()
    engine.setProperty('rate', 200)
    # Можно добавить выбор голоса, если нужно:
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[2].id)

    engine.say(text)
    engine.runAndWait()
    engine.stop()


def listen() -> str:
    """Функция прослушивания: открывает микрофон, ловит фразу и закрывает его"""
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
    rec = KaldiRecognizer(model, 16000)

    print(">>> Слушаю...")

    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            if result['text']:
                # Закрываем ресурсы микрофона сразу после распознавания
                stream.stop_stream()
                stream.close()
                p.terminate()
                return result['text']