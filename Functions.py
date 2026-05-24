import pyttsx3
import requests
import speech_recognition as sr
import wikipedia
from openai import OpenAI

# ================= Настройки =================
DEEPSEEK_API_KEY = "sk-dc2fcc7ab8f74bafa0be71c87dc52ca7"
WEATHER_API_KEY = "14ebd344becc6b5f6d0c5da75f921119"
WAKE_WORD = "альфа"
# =============================================
class AlphaAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.tts_engine = pyttsx3.init()
        self.client = OpenAI(DEEPSEEK_API_KEY)

    def get_weather(self):
        """Запрос данных о погоде в Томске через API OpenWeatherMap"""
        city = "Tomsk,RU"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        
        try:
            res = requests.get(url).json()
            if res.get("cod") != 200:
                return "Не удалось получить данные о погоде."
            
            temp = round(res["main"]["temp"])
            status = res["weather"][0]["description"]
            return f"В Томске сейчас {temp} градусов, {status}."
        except:
            return "Ошибка связи с метеослужбой."

    def get_wiki(self, query):
        """Поиск краткого определения (1 предложение) в Википедии"""
        prefixes = ["что такое", "кто такой", "википедия", "найди"]
        search_term = query
        for p in prefixes:
            search_term = search_term.replace(p, "")
        
        try:
            return wikipedia.summary(search_term.strip(), sentences=1)
        except wikipedia.DisambiguationError:
            return "Найдено слишком много совпадений. Уточните запрос."
        except wikipedia.PageError:
            return "Я не нашла такой статьи в Википедии."
        except:
            return "Ошибка при поиске в энциклопедии."

    def ask_ai(self, question):
        """Обращение к нейросети DeepSeek для сложных вопросов"""
        print("[...] Запрос к нейросети")
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": question}],
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка нейросети: {e}"
        

    