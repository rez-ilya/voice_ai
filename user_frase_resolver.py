from rapidfuzz import fuzz, process
# import web     # Участник 3
import open_files_os
import ai_integration

# Словарь намерений
INTENTS = {
    'weather': ['погода', 'прогноз', 'температура', 'градусы', 'холодно'],
    'wiki': ['кто такой', 'что такое', 'расскажи о', 'найди информацию'],
    'mail': ['почта', 'письма', 'проверь ящик', 'новые сообщения'],
    'apps': ['открой', 'запусти', 'включи'],
    'system':['выключи компьютер','отруби компьютер','выруби компьютер','отключи компьютер'],
    'time': ['время','час','времени']
}


def resolve_intent(text: str) -> str:    
    best_intent = None
    max_score = 0

    #Ищем совпадения с заранее подготовленными намерениями
    for intent, keywords in INTENTS.items():
        # Сравниваем входную фразу со списком ключевых слов
        # score_cutoff=70 позволяет сразу отсекать плохие варианты
        result = process.extractOne(text, keywords, scorer=fuzz.WRatio)
        
        if result and result[1] > max_score:
            max_score = result[1]
            best_intent = intent
    
    #Порог уверенности
    if max_score < 70:
        print(">>> Команда не в списке, обращаюсь к ИИ...")
        return ai_integration.ask_ai(text)

    #Погода
    if best_intent == 'weather':
        return 'когда будет модуль погоды, она тут появится'
        #return web.get_weather()
    
    #Поиск в википедии
    elif best_intent == 'wiki':
        # Вырезаем ключевые слова, чтобы оставить только запрос (н-р: "кто такой Пушкин")
        query = text
        for word in INTENTS['wiki']:
            query = query.replace(word, "").strip()
        return 'Поиск инфы в википедии'
    
    #вывести последние несколько тем писем с почты
    elif best_intent == 'mail':
        return open_files_os.check_mail()
    
    #Включение всех приложений
    elif best_intent == 'apps':
        # Пытаемся понять, какое приложение запустить
        return open_files_os.run_app(text)
    
    #Выключение пк
    elif best_intent == 'system':
        return open_files_os.shutdown_pc()
    
    #Время
    elif best_intent == 'time':
        return open_files_os.get_time()
    
    else:
        return "Команда распознана, но обработчик еще не настроен."

print(resolve_intent("сколько сейчас"))