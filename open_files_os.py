import os
# import ctypes
import imaplib
import email
import webbrowser
from email.header import decode_header
from datetime import datetime
import config
import urllib.parse

# Справочник ТОЛЬКО для сложных путей или специфических алиасов
APPS = {
    "калькулятор": "calculator:",
    "блокнот": "notepad.exe",
    "браузер": "chrome.exe",
    "ютуб": "https://www.youtube.com",
    "погода": "https://yandex.ru/pogoda",
    "музыку": "music:",
    "эпл мьюзик": "music:",
    "яндекс музыка": "https://music.yandex.ru",
    "телеграмм": "tg:",
    "параметры компьютера": "ms-settings:",
    "часы": "ms-clock:",
    "холст": "ms-paint:",
    # "фотографии": "ms-photos:",
    # "календарь": "ms-calendar:"
}

# # Коды виртуальных клавиш Windows для управления медиа
# VK_MEDIA_NEXT_TRACK = 0xB0
# VK_MEDIA_PREV_TRACK = 0xB1
# VK_MEDIA_PLAY_PAUSE = 0xB3

# def control_music(key_code):
#     """Отправляет системное нажатие медиа-клавиши."""
#     ctypes.windll.user32.keybd_event(key_code, 0, 0, 0)
#     ctypes.windll.user32.keybd_event(key_code, 0, 2, 0)

# def handle_music_commands(command: str):
#     """Обрабатывает команды управления воспроизведением."""
#     if "включи" in command or "поставь" in command:
#         if "любимое" in command or "музыку" in command:
#             try:
#                 os.startfile("music:")
#             except Exception:
#                 pass
#             control_music(VK_MEDIA_PLAY_PAUSE)
#             return "Включаю вашу музыку."
        
#     if "пауза" in command or "стоп" in command:
#         control_music(VK_MEDIA_PLAY_PAUSE)
#         return "Ставлю музыку на паузу."

#     if "следующий" in command or "дальше" in command:
#         control_music(VK_MEDIA_NEXT_TRACK)
#         return "Переключаю на следующий трек."
    
#     return None

def run_app(user_command: str, search_query: str = None):
    cmd = user_command.lower().strip()
    
    # # 1. Перехват медиа-команд (пауза, треки)
    # music_result = handle_music_commands(cmd)
    # if music_result:
    #     return music_result

    # 2. ОБРАБОТКА ПОИСКОВЫХ ЗАПРОСОВ (Сюда управление отправляет только ИИ)
    if search_query:
        print(f">>> Запрос на поиск: {search_query} в приложении {cmd}")
        encoded_query = urllib.parse.quote(search_query)
        
        if cmd in ["youtube", "ютуб"]:
            webbrowser.open(f"https://www.youtube.com/results?search_query={encoded_query}")
            return f"Включаю {search_query} на Ютубе."
        else:
            webbrowser.open(f"https://www.google.com/search?q={encoded_query}")
            return f"Ищу в интернете: {search_query}."
    
    # 3. СИСТЕМНЫЕ СХЕМЫ WINDOWS (Умный вызов от GigaChat: ms-photos, ms-calendar)
    if "ms-" in cmd:
        print(f">>> Вызов UWP-приложения Windows через протокол: {cmd}")
        os.system(f"start {cmd}:")
        return f"Запускаю."

    # 4. ЭТАП ОФФЛАЙН 1: Поиск в локальном словаре жестких соответствий
    # Работает БЕЗ ИИ, когда говоришь "открой блокнот"
    for app_name, path in APPS.items():
        if app_name in cmd:
            print(f">>> Локальный словарь: Запуск жесткого алиаса '{app_name}' -> '{path}'")
            try:
                os.startfile(path)
                return f"Окей, запускаю {app_name}."
            except Exception:
                if os.system(f'start "" "{path}"') == 0:
                    return f"Окей, запускаю {app_name}."
                
    # 5. Очистка команды от мусорных триггеров для динамического запуска
    clean_cmd = cmd
    for word in ["открой", "запусти", "включи", "программу", "приложение"]:
        clean_cmd = clean_cmd.replace(word, "")
    clean_cmd = clean_cmd.strip()
    
    if not clean_cmd:
        return None

    # 6. ЭТАП ОФФЛАЙН 2: ДИНАМИЧЕСКИЙ ЗАПУСК И ПРОТОКОЛЫ
    # Если мы в оффлайне, и юзер сказал английское имя (например, "discord")
    # try:
    #     print(f">>> Динамический запуск: Пробую системную команду 'start {clean_cmd}'")
    #     if os.system(f'start "" "{clean_cmd}"') == 0:
    #         return f"Открываю {clean_cmd}."
    # except Exception:
    #     pass

    # Проверка URI-лаунчеров (steam://, discord://)
    KNOWN_PROTOCOLS = ["steam", "discord", "tg", "spotify", "epicgames"]
    if clean_cmd in KNOWN_PROTOCOLS:
        try:
            print(f">>> Динамический запуск: Пробую проверенный протокол {clean_cmd}://")
            os.startfile(f"{clean_cmd}://")
            return f"Запускаю {clean_cmd}."
        except Exception:
            pass

    # 7. ФИНАЛЬНЫЙ РЕЗЕРВНЫЙ ВЫХОД
    # Если код дошел до этой точки, значит ЛОКАЛЬНО мы запустить ничего не смогли.
    # Если это был первый (локальный) проход из intent_resolver, функция вернет None, 
    # и intent_resolver перенаправит этот запрос в GigaChat.
    print(f">>> Локальный запуск не удался для '{clean_cmd}'.")
    return None

def check_mail():
    mail = None
    try:
        mail = imaplib.IMAP4_SSL(config.IMAP_SERVER)
        mail.login(config.MAIL_USER, config.MAIL_PASS)
        mail.select("INBOX", readonly=True)
        status, response = mail.search(None, 'UNSEEN')
        if status != 'OK': 
            return "Не удалось получить список писем."
            
        unread_ids = response[0].split()
        count = len(unread_ids)
        if count == 0: 
            return "Новых писем нет."
        
        last_ids = unread_ids[-3:][::-1]
        subjects = []
        for mail_id in last_ids:
            res, msg_data = mail.fetch(mail_id, '(BODY[HEADER.FIELDS (SUBJECT)])')
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            subject, encoding = decode_header(msg.get("Subject", "Без темы"))[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8")
            subjects.append(subject)
            
        return f"У вас {count} новых писем. Последние темы: {', '.join(subjects)}."
    except Exception as e: 
        return f"Ошибка при проверке почты: {e}"
    finally:
        if mail:
            try:
                if mail.state == 'SELECTED': 
                    mail.close()
                mail.logout()
            except: 
                pass

def shutdown_pc():
    os.system("shutdown /s /t 10")
    return "Компьютер будет выключен через 10 секунд. До свидания!"

def get_time():
    now = datetime.now()
    return f"Сейчас {now.hour:02d}:{now.minute:02d}"