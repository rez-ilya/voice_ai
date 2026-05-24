import os
import ctypes
import imaplib
import email
from email.header import decode_header
from datetime import datetime
import config

# Коды виртуальных клавиш Windows для управления медиа
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3

# Справочник оставляем ТОЛЬКО для сложных путей или специфических алиасов
APPS = {
    "калькулятор": "calculator:",
    # "блокнот": "notepad.exe",
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
    "фотографии": "ms-photos:",
    "календарь": "ms-calendar:"
}

def control_music(key_code):
    """Отправляет системное нажатие медиа-клавиши."""
    ctypes.windll.user32.keybd_event(key_code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(key_code, 0, 2, 0)

def handle_music_commands(command: str):
    """Обрабатывает команды управления воспроизведением."""
    if "включи" in command or "поставь" in command:
        if "любимое" in command or "музыку" in command:
            os.startfile("music:")
            control_music(VK_MEDIA_PLAY_PAUSE)
            return "Включаю вашу музыку в Apple Music."
        
    if "пауза" in command or "стоп" in command:
        control_music(VK_MEDIA_PLAY_PAUSE)
        return "Ставлю музыку на паузу."

    if "следующий" in command or "дальше" in command:
        control_music(VK_MEDIA_NEXT_TRACK)
        return "Переключаю на следующий трек."
    
    return None

def run_app(user_command: str):
    cmd = user_command.lower().strip()
    
    # Проверяем музыку
    music_result = handle_music_commands(cmd)
    if music_result:
        return music_result

    # ЭТАП 1: Ищем в локальном словаре базовых программ
    for app_name, path in APPS.items():
        if app_name in cmd:
            print(f">>> Словарь APPS: Найдено совпадение '{app_name}'. Пробую запустить '{path}'...")
            try:
                exit_code = os.system(f'start "" "{path}"')
                if exit_code == 0:
                    return f"Окей, запускаю {app_name}."
            except Exception:
                pass
                
    # ЭТАП 2: ДИНАМИЧЕСКИЙ ЗАПУСК
    clean_cmd = cmd
    for word in ["открой", "запусти", "включи", "программу", "приложение"]:
        clean_cmd = clean_cmd.replace(word, "")
    clean_cmd = clean_cmd.strip()
    
    if not clean_cmd:
        return None # Если команда пустая, возвращаем None для ухода в ИИ

    # Шаг А: Пробуем запустить как URI-протокол (steam://, discord://)
    try:
        print(f">>> Динамический запуск: Пробую протокол {clean_cmd}://")
        os.startfile(f"{clean_cmd}://")
        return f"Запускаю {clean_cmd}."
    except Exception:
        # Шаг Б: Если протокол не поддерживается, запускаем через системную команду start
        try:
            print(f">>> Динамический запуск: Пробую системную команду 'start {clean_cmd}'")
            exit_code = os.system(f'start "" "{clean_cmd}"')
            
            if exit_code == 0:
                return f"Открываю {clean_cmd}."
        except Exception:
            pass

    # КРИТИЧЕСКИЙ МОМЕНТ: Если ни один способ выше не сработал
    print(f">>> Локальный запуск для '{clean_cmd}' не удался. Передаю управление ИИ...")
    return None

def check_mail():
    mail = None
    try:
        mail = imaplib.IMAP4_SSL(config.IMAP_SERVER)
        mail.login(config.MAIL_USER, config.MAIL_PASS)
        mail.select("INBOX", readonly=True)
        status, response = mail.search(None, 'UNSEEN')
        if status != 'OK': return "Не удалось получить список писем."
        unread_ids = response[0].split()
        count = len(unread_ids)
        if count == 0: return "Новых писем нет."
        
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
    except Exception as e: return f"Ошибка при проверке почты: {e}"
    finally:
        if mail:
            try:
                if mail.state == 'SELECTED': mail.close()
                mail.logout()
            except: pass

def shutdown_pc():
    os.system("shutdown /s /t 10")
    return "Компьютер будет выключен через 10 секунд. До свидания!"

def get_time():
    now = datetime.now()
    return f"Сейчас {now.hour} {now.minute}"