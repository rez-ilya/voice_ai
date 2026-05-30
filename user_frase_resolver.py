from rapidfuzz import fuzz, process
import open_files_os
import ai_integration
import weather_wiki

# Инициализируем класс локальных инструментов
weather_tools = weather_wiki.AlphaAssistant()

# Словарь намерений
INTENTS = {
    'weather': ['погода', 'прогноз', 'температура', 'градусы', 'холодно'],
    'wiki': ['кто такой', 'что такое', 'расскажи', 'википедия'],
    'mail': ['почта', 'письма', 'проверь ящик', 'новые сообщения'],
    'apps': ['открой', 'запусти', 'включи'],
    'system': ['выключи компьютер', 'отруби компьютер', 'выруби компьютер', 'отключи компьютер'],
    'time': ['время', 'час', 'времени']
}

def resolve_intent(text: str) -> str:    
    best_intent = None
    max_score = 0

    # Ключевые слова для поиска (их можно вынести в список)
    search_keywords = ["найди", "поищи", "гугл", "google", "яндекс"]
    
    # Если в тексте есть команды поиска, мы ПРИНУДИТЕЛЬНО отдаем это в ИИ
    if any(keyword in text.lower() for keyword in search_keywords):
        print(">>> Обнаружен запрос на поиск в интернете. Передаю в ИИ...")
        return ai_integration.ask_ai(text)
    
    # 1. Ищем совпадения с заранее подготовленными намерениями через нечеткое сравнение
    for intent, keywords in INTENTS.items():
        result = process.extractOne(text, keywords, scorer=fuzz.WRatio)
        if result and result[1] > max_score:
            max_score = result[1]
            best_intent = intent
    
    local_result = None

    # 2. Если уверенность высокая (>= 70), строго выполняем команду ЛОКАЛЬНО БЕЗ ИИ
    if max_score >= 70:
        print(f">>> Сработал локальный интент: {best_intent} ({max_score}%)")
        
        # Погода (теперь реальная!)
        if best_intent == 'weather':
            local_result = weather_tools.get_weather()
        
        # Поиск в википедии
        elif best_intent == 'wiki':
            query = text.lower()
            for word in INTENTS['wiki']:
                query = query.replace(word, "").strip()
            
            if query:
                local_result = weather_tools.get_wiki(query)
            else:
                local_result = "Вы не уточнили, что именно нужно найти в Википедии."
        
        # Почта
        elif best_intent == 'mail':
            local_result = open_files_os.check_mail()
        
        # Запуск приложений
        elif best_intent == 'apps':
            local_result = open_files_os.run_app(text)
        
        # Выключение ПК
        elif best_intent == 'system':
            local_result = open_files_os.shutdown_pc()
        
        # Время
        elif best_intent == 'time':
            local_result = open_files_os.get_time()

    # 3. КРИТИЧЕСКИЙ УЗЕЛ: Если скор низкий ИЛИ локальный скрипт не справился (вернул None)
    # Например, на фразу "включи видео про котиков" локальный скрипт вернет None из-за русских букв.
    if max_score < 70 or local_result is None:
        print(">>> Локальные сценарии не справились или не найдены. Обращаюсь к GigaChat...")
        
        # Запрашиваем ИИ (он вернет уже выполненный результат работы функции, либо просто текст)
        ai_result = ai_integration.ask_ai(text)
        return ai_result

    # 4. Если локальный сценарий отработал успешно — возвращаем его ответ
    return local_result