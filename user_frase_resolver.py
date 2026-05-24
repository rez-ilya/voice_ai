from rapidfuzz import fuzz, process
import open_files_os
import ai_integration

# Словарь намерений
INTENTS = {
    'weather': ['погода', 'прогноз', 'температура', 'градусы', 'холодно'],
    'wiki': ['кто такой', 'что такое', 'расскажи о', 'найди информацию'],
    'mail': ['почта', 'письма', 'проверь ящик', 'новые сообщения'],
    'apps': ['открой', 'запусти', 'включи'],
    'system': ['выключи компьютер', 'отруби компьютер', 'выруби компьютер', 'отключи компьютер'],
    'time': ['время', 'час', 'времени']
}


def resolve_intent(text: str) -> str:    
    best_intent = None
    max_score = 0

    # 1. Ищем совпадения с заранее подготовленными намерениями
    for intent, keywords in INTENTS.items():
        # Сравниваем входную фразу со списком ключевых слов
        result = process.extractOne(text, keywords, scorer=fuzz.WRatio)
        
        if result and result[1] > max_score:
            max_score = result[1]
            best_intent = intent
    
    # Переменная для перехвата результатов локального выполнения
    local_result = None

    # 2. Если уверенность высокая, пробуем выполнить команду локально
    if max_score >= 70:
        print(f">>> Сработал локальный интент: {best_intent} ({max_score}%)")
        
        # Погода
        if best_intent == 'weather':
            local_result = 'когда будет модуль погоды, она тут появится'
            # local_result = web.get_weather()
        
        # Поиск в википедии
        elif best_intent == 'wiki':
            query = text
            for word in INTENTS['wiki']:
                query = query.replace(word, "").strip()
            local_result = 'Поиск инфы в википедии'
        
        # Вывести последние темы писем с почты
        elif best_intent == 'mail':
            local_result = open_files_os.check_mail()
        
        # Включение всех приложений
        elif best_intent == 'apps':
            # Пытаемся понять, какое приложение запустить
            local_result = open_files_os.run_app(text)
        
        # Выключение пк
        elif best_intent == 'system':
            local_result = open_files_os.shutdown_pc()
        
        # Время
        elif best_intent == 'time':
            local_result = open_files_os.get_time()

    # 3. КРИТИЧЕСКИЙ УЗЕЛ: Если скор < 70 ИЛИ локальный скрипт вернул None (не смог обработать)
    if max_score < 70 or local_result is None:
        print(">>> Локальные сценарии не справились или не найдены. Обращаюсь к GigaChat...")
        
        # Запрашиваем ИИ (поддерживает как старый текстовый формат, так и новые Tools/JSON)
        ai_result = ai_integration.ask_ai(text)
        
        # Если ai_integration уже переписан на структурированный вывод (Tools)
        if isinstance(ai_result, dict):
            if ai_result.get("type") == "text":
                return ai_result.get("content")
                
            elif ai_result.get("type") == "function":
                func_name = ai_result.get("name")
                args = ai_result.get("arguments", {})
                print(f">>> GigaChat вызвал функцию: {func_name} с аргументами {args}")
                
                if func_name == "run_app":
                    cmd_param = args.get("user_command", text)
                    res = open_files_os.run_app(cmd_param)
                    return res if res else f"Я понял, что нужно запустить {cmd_param}, но этой программы нет в моем списке."
                elif func_name == "check_mail":
                    return open_files_os.check_mail()
                elif func_name == "get_time":
                    return open_files_os.get_time()
                elif func_name == "shutdown_pc":
                    return open_files_os.shutdown_pc()
                    
            return "Ошибка интерпретации команды ИИ."
        
        # Если ai_integration пока возвращает обычную строку текста
        return ai_result

    # 4. Если локальный скрипт отработал успешно — возвращаем его строку ответа
    return local_result


# Тест-драйв работы резолвера
if __name__ == "__main__":
    print(resolve_intent("сколько сейчас времени"))