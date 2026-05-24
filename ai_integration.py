import json
import re
from gigachat import GigaChat
import config
import open_files_os
import weather_wiki

# Инициализируем класс, чтобы использовать его внутри вызовов инструментов GigaChat
weather_tools = weather_wiki.AlphaAssistant()

# ЧИСТЫЙ СПРАВОЧНИК ФУНКЦИЙ ДЛЯ ИИ
GIGACHAT_FUNCTIONS = [
    {
        "name": "run_app",
        "description": "Запускает приложение или открывает сайт. Если пользователь просит найти конкретное видео, трек или информацию, ОБЯЗАТЕЛЬНО передавай этот запрос в параметр search_query.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_command": {
                    "type": "string",
                    "description": "Английское системное название программы или сайта (например: 'youtube', 'chrome', 'notepad', 'google')."
                },
                "search_query": {
                    "type": "string",
                    "description": "Поисковый запрос на русском языке, если пользователь просит что-то найти (например: 'видео про котиков', 'клип rammstein')."
                }
            },
            "required": ["user_command"]
        }
    },
    {
        "name": "get_weather",
        "description": "Получает текущую сводку погоды для города Томск.",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "get_wiki",
        "description": "Ищет краткую информацию в Википедии, когда пользователь спрашивает факты, определения или биографию людей.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Предмет поиска (например: 'синхрофазотрон', 'Илон Маск')."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "check_mail",
        "description": "Проверяет почтовый ящик пользователя на наличие новых писем.",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "get_time",
        "description": "Возвращает текущее системное время компьютера.",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "shutdown_pc",
        "description": "Выключает компьютер пользователя.",
        "parameters": {"type": "object", "properties": {}}
    }
]

def ask_ai(question: str) -> str:
    cmd = question.lower()
    
    # Список триггеров для понимания: ИИ должен использовать функции или просто общаться?
    ACTION_KEYWORDS = [
        'открой', 'запусти', 'включи', 'поставь', 'выключи', 'выруби', 'отруби', 
        'проверь', 'узнай', 'погода', 'время', 'письма', 'почта',
        'что такое', 'кто такой', 'википедия', 'найди информацию', 'расскажи о'
    ]
    is_action_command = any(word in cmd for word in ACTION_KEYWORDS)
    
    if is_action_command:
        # Промпт чисто для разбора запутанных фраз (без текстовых примеров, чтобы ИИ не ленился)
        system_prompt = (
            "Ты — системный переключатель функций для ассистента Джарвиса. Твоя единственная задача — вызывать инструменты.\n"
            "Внимательно сопоставляй сложный запрос пользователя с описанием доступных функций и вызывай нужную."
        )
    else:
        # Режим обычного диалога
        system_prompt = "Ты — дружелюбный бортовой ИИ-ассистент Джарвис. Отвечай очень кратко и емко (1-2 предложения)."

    try:
        with GigaChat(credentials=config.GIGACHAT_CREDENTIALS, scope="GIGACHAT_API_PERS", verify_ssl_certs=False) as giga:
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ]
            }
            
            # Включаем нативную поддержку функций Сбера, только если распознали команду
            if is_action_command:
                payload["functions"] = GIGACHAT_FUNCTIONS
                payload["function_call"] = "auto"
            
            response = giga.chat(payload)
            message = response.choices[0].message
            
            # === СПОСОБ 1: АППАРАТНЫЙ ВЫЗОВ (РЕКОМЕНДУЕМЫЙ GIGACHAT) ===
            if hasattr(message, "function_call") and message.function_call:
                func_name = message.function_call.name
                raw_args = message.function_call.arguments
                args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                
                print(f">>> GigaChat вызвал инструмент '{func_name}' с аргументами {args}")
                
                if func_name == "run_app":
                    return open_files_os.run_app(args.get("user_command"), args.get("search_query"))
                elif func_name == "get_weather":
                    return weather_tools.get_weather()
                elif func_name == "get_wiki":
                    return weather_tools.get_wiki(args.get("query"))
                elif func_name == "get_time":
                    return open_files_os.get_time()
                elif func_name == "check_mail":
                    return open_files_os.check_mail()
                elif func_name == "shutdown_pc":
                    return open_files_os.shutdown_pc()

            # === СПОСОБ 2: НЕУБИВАЕМЫЙ ТЕКСТОВЫЙ ПЕРЕХВАТЧИК ===
            # Оставляем на случай, если ИИ проигнорирует JSON-инструменты и напишет код строкой в контент
            content = message.content.strip() if message.content else ""
            
            for func in ["run_app", "get_weather", "get_wiki", "get_time", "check_mail", "shutdown_pc"]:
                if func in content:
                    match = re.search(f"{func}\s*\((.*?)\)", content)
                    if match:
                        inside_brackets = match.group(1)
                        parts = [p.strip().strip("'\"") for p in inside_brackets.split(',', 1)] if inside_brackets else []
                        
                        print(f">>> Текстовый перехватчик поймал команду: {func}({inside_brackets})")
                        
                        if func == "run_app":
                            return open_files_os.run_app(parts[0] if len(parts) > 0 else "", parts[1] if len(parts) > 1 else None)
                        elif func == "get_weather":
                            return weather_tools.get_weather()
                        elif func == "get_wiki":
                            return weather_tools.get_wiki(parts[0] if len(parts) > 0 else "")
                        elif func == "get_time":
                            return open_files_os.get_time()
                        elif func == "check_mail":
                            return open_files_os.check_mail()
                        elif func == "shutdown_pc":
                            return open_files_os.shutdown_pc()

            # Если это был просто разговор, возвращаем обычный текстовый ответ ИИ
            return content
                    
    except Exception as e:
        return f"Ошибка связи с Джарвисом: {e}"