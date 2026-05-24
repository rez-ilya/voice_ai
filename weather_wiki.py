import requests

class AlphaAssistant:
    def __init__(self):
        pass

    def get_weather(self):
        """Запрос данных о погоде в Томске через бесплатный сервис wttr.in"""
        city = "Tomsk"
        url = f"https://wttr.in/{city}?format=j1"
        headers = {
            "Accept-Language": "ru"
        }

        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code != 200:
                return "Не удалось получить данные о погоде."
                
            res = response.json()
            current = res["current_condition"][0]
            temp = current["temp_C"]
            
            if "lang_ru" in current and current["lang_ru"]:
                status = current["lang_ru"][0]["value"]
            else:
                status = current["weatherDesc"][0]["value"]
                
            return f"В Томске сейчас {temp} градусов, {status.lower()}."
            
        except Exception as e:
            print(f"[ОШИБКА ПОГОДЫ]: {e}")
            return "Ошибка связи с метеослужбой. Проверьте интернет."

    def get_wiki(self, query):
        """Прямой поиск в Википедии с автоподбором точного названия статьи"""
        import re

        # 1. Очистка входящего запроса от мусорных слов
        search_term = query.lower().strip()
        prefixes = ["что такое", "кто такой", "википедия", "найди", "расскажи о", "поиск"]
        for p in prefixes:
            if p in search_term:
                search_term = search_term.replace(p, "").strip()

        if not search_term:
            return "Вы не уточнили, что именно нужно найти."

        print(f"[...] Ищем точное название в Википедии для: {search_term}")

        url = "https://ru.wikipedia.org/w/api.php"
        headers = {
            "User-Agent": "AlphaVoiceAssistant/2.0 (my_bot@example.com)"
        }

        try:
            # СНАЧАЛА ИЩЕМ ТОЧНОЕ НАЗВАНИЕ СТАТЬИ
            search_params = {
                "action": "query",
                "list": "search",
                "srsearch": search_term,
                "format": "json",
                "srlimit": 1  # Нам нужен только 1 самый точный результат
            }

            search_res = requests.get(url, params=search_params, headers=headers, timeout=5).json()
            search_hits = search_res.get("query", {}).get("search", [])

            if not search_hits:
                return f"Я не нашла в Википедии статей, похожих на {search_term}."

            # Получаем идеальное название статьи (например, "Заяц-беляк" вместо "заяц беляк")
            exact_title = search_hits[0]["title"]
            print(f"[...] Найдена статья: {exact_title}. Выкачиваем текст...")

            # ТЕПЕРЬ КАЧАЕМ ТЕКСТ СТАТЬИ ПО ТОЧНОМУ НАЗВАНИЮ
            params = {
                "action": "query",
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "titles": exact_title,
                "format": "json"
            }

            res = requests.get(url, params=params, headers=headers, timeout=5).json()
            pages = res.get("query", {}).get("pages", {})

            page_id = list(pages.keys())[0]
            full_text = pages[page_id].get("extract", "")

            if not full_text:
                return f"Статья про {exact_title} найдена, но я не смогла прочитать её содержимое."

            # 3. ФИЛЬТРАЦИЯ МУСОРА (Вырезаем скобки, даты, латынь)
            cleaned_text = re.sub(r'\s*\([^)]*\)', '', full_text)
            cleaned_text = re.sub(r'\s*\[[^\]]*\]', '', cleaned_text)

            # 4. Нарезка на предложения
            sentences = re.split(r'(?<!\w\.\w.)(?<![А-ЯЁ]\.)(?<=\.|\?)\s', cleaned_text)
            result_sentences = [s.strip() for s in sentences if s.strip()][:2]

            if not result_sentences:
                return "Не удалось составить краткое описание."

            return " ".join(result_sentences)

        except Exception as e:
            print(f"[КРИТИЧЕСКАЯ ОШИБКА ВИКИ]: {e}")
            return "Не удалось получить ответ из Википедии."