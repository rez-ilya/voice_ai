import json
from gigachat import GigaChat
import config
import re
import open_files_os
import datetime  # Добавили для работы со временем

# Справочник инструментов (Tools)
ASSISTANT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_app",
            "description": "Запускает приложение или сайт. Обязательно очищай название от мусора и переводи в правильный системный формат (например, 'с тим' -> 'steam', 'дискорд' -> 'discord').",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_command": {
                        "type": "string",
                        "description": "Чистое английское или системное название программы (например: 'steam', 'chrome', 'discord', 'vk')."
                    }
                },
                "required": ["user_command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_mail",
            "description": "Проверяет почтовый ящик пользователя.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Возвращает текущее системное время.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "shutdown_pc",
            "description": "Выключает компьютер пользователя.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

def ask_ai(question: str) -> str:  # Теперь функция всегда возвращает строку с текстом
    cmd = question.lower()
    
    # 1. ЛОКАЛЬНЫЙ ФИЛЬТР: Список слов, которые однозначно означают действие
    ACTION_KEYWORDS = [
        'открой', 'запусти', 'включи', 'поставь', 'выключи', 
        'выруби', 'отруби', 'проверь', 'узнай', 'погода', 'время', 'письма'
    ]
    
    is_action_command = any(word in cmd for word in ACTION_KEYWORDS)
    
    # 2. ДИНАМИЧЕСКИЙ ВЫБОР ПРОМПТА И ИНСТРУМЕНТОВ
    if is_action_command:
        print(">>> Локальный фильтр: Определена КОМАНДА. Включаю режим триггера функций...")
        system_prompt = (
            "Ты — системный переключатель функций для ассистента Джарвиса. Твоя единственная задача — вызывать инструменты (tools).\n\n"
            "ВАЖНО: Пользователь использует плохой голосовой ввод, поэтому названия приложений будут приходить с дикими ошибками и опечатками. "
            "Ты должен ИСПРАВЛЯТЬ их на лету и передавать в параметр 'user_command' строго ПРАВИЛЬНОЕ английское или системное название программы.\n"
            "Примеры исправления ошибок:\n"
            "- 'открой с тим', 'запусти стим', 'с тимка' -> вызов run_app(user_command='steam')\n"
            "- 'открой дискард', 'включи дискорд' -> вызов run_app(user_command='discord')\n"
            "- 'гугл хром', 'запусти хром', 'браузер' -> вызов run_app(user_command='chrome')\n"
            "- 'запусти вк', 'открой вконтакте' -> вызов run_app(user_command='vk')\n\n"
            "Ты НЕ имеешь права писать текст отказа или говорить, что у тебя нет доступа. Ты ОБЯЗАН вызвать run_app!"
        )
        tools_to_send = ASSISTANT_TOOLS
    else:
        print(">>> Локальный фильтр: Определен РАЗГОВОР. Включаю режим собеседника...")
        system_prompt = "Ты — дружелюбный бортовой ИИ-ассистент Джарвис. Отвечай на вопросы пользователя очень кратко и емко (1-2 sentences)."
        tools_to_send = None

    # 3. ЗАПРОС К GIGACHAT
    try:
        with GigaChat(credentials=config.GIGACHAT_CREDENTIALS, 
                      scope="GIGACHAT_API_PERS", 
                      verify_ssl_certs=False) as giga:
            
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ]
            }
            
            if tools_to_send:
                payload["tools"] = tools_to_send
            
            response = giga.chat(payload)
            message = response.choices[0].message
            
            # 4. ОБРАБОТКА РЕЗУЛЬТАТА И МГНОВЕННОЕ ВЫПОЛНЕНИЕ
            
            # Вариант А: Официальный вызов функции через Tools (Штатный режим)
            if hasattr(message, "function_call") and message.function_call:
                func_name = message.function_call.name
                raw_args = message.function_call.arguments
                
                if isinstance(raw_args, str):
                    try: args = json.loads(raw_args)
                    except Exception: args = {"user_command": question}
                else:
                    args = raw_args if raw_args else {}
                
                print(f">>> ИИ затребовал вызов функции '{func_name}' с аргументами {args}")
                
                # Выполняем команду прямо здесь через наши модули!
                if func_name == "run_app":
                    app_name = args.get("user_command")
                    return open_files_os.run_app(app_name)  # Запускает приложение и возвращает статус текста
                    
                elif func_name == "get_time":
                    current_time = datetime.datetime.now().strftime("%H:%M")
                    return f"Сейчас {current_time}."
                    
                elif func_name == "check_mail":
                    return "Я проверил почту. Новых писем нет."
                    
                elif func_name == "shutdown_pc":
                    import os
                    os.system("shutdown /s /t 5")
                    return "Выключаю компьютер через 5 секунд. Сохраните работу."
            
            # Вариант Б: ПЕРЕХВАТЧИК (Костыль-спаситель для текстовых галлюцинаций ИИ)
            content = message.content.strip() if message.content else ""
            if "run_app" in content:
                match = re.search(r"run_app\(['\"](.*?)['\"]\)", content)
                if match:
                    extracted_app = match.group(1)
                    print(f">>> Перехватчик: ИИ написал функцию текстом. Выполняю run_app('{extracted_app}')...")
                    return open_files_os.run_app(extracted_app) # Выполняем запуск

            # Вариант В: Если это обычный разговорный текст
            return content
                    
    except Exception as e:
        return f"Ошибка обработки запроса внутри ИИ-модуля: {e}"