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

# Справочник программ
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
            # Открываем приложение (если закрыто) и жмем Play
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
    cmd = user_command.lower()
    
    # Проверяем, не является ли команда музыкальной
    music_result = handle_music_commands(cmd)
    if music_result:
        return music_result

    # Стандартный запуск приложений из справочника
    for app_name, path in APPS.items():
        if app_name in cmd:
            try:
                # os.startfile работает в Windows как двойной клик, не блокируя выполнение скрипта
                os.startfile(path)
                return f"Окей, запускаю {app_name}."
            except Exception as e:
                return f"Не удалось запустить {app_name}. Ошибка: {e}"
                
    return "Я не нашел такую программу в своем списке. Добавь её в настройки."

def check_mail():
    mail = None
    try:
        # В файле config хранится пароль логин, пароль и сервер конкретной почты.
        # 1. Соединение с сервером по защищенному протоколу SSL
        mail = imaplib.IMAP4_SSL(config.IMAP_SERVER)
        
        # 2. Авторизация
        mail.login(config.MAIL_USER, config.MAIL_PASS)
        
        # 3. Выбор папки в режиме "только чтение"
        mail.select("INBOX", readonly=True)
        
        # 4. Поиск ID непрочитанных писем. 
        # Флаг 'UNSEEN' ищет сообщения, которые еще не были открыты
        status, response = mail.search(None, 'UNSEEN')
        
        if status != 'OK':
            return "Не удалось получить список писем."

        # Данные приходят в виде списка байтовых строк, разделяем их
        unread_ids = response[0].split()
        count = len(unread_ids)

        if count == 0:
            return "Новых писем нет."
        
        # Извлекаем темы до 3-х последних писем
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

        subjects_text = ", ".join(subjects)
        return f"У вас {count} новых писем. Последние темы: {subjects_text}."

    except Exception as e:
        return f"Ошибка при проверке почты: {e}"
    finally:
        if mail:
            try:
                # close() можно вызывать только если папка была успешно выбрана
                if mail.state == 'SELECTED':
                    mail.close()
                mail.logout()
            except:
                # Если произошла ошибка авторизации, logout может не сработать, просто игнорируем
                pass

def shutdown_pc():
    os.system("shutdown /s /t 10")
    return "Компьютер будет выключен через 10 секунд. До свидания!"

def get_time():
    now = datetime.now()
    return f"Сейчас {now.hour} {now.minute}"

if __name__ == "__main__":
    
    # print(run_app("открой музыку"))
    # # Список фраз для комплексной проверки ассистента
    # test_commands = [
    #     "открой калькулятор",       # Проверка запуска UWP
    #     "включи музыку",            # Проверка handle_music_commands (Play)
    #     "пауза",                    # Проверка handle_music_commands (Pause)
    #     "следующий трек",           # Проверка handle_music_commands (Next)
    #     "открой телеграмм",         # Проверка словаря APPS
    #     "покажи фотографии"         # Проверка системного протокола ms-photos
    # ]

    # print("=== ТЕСТИРОВАНИЕ КОМАНД (run_app) ===")
    # for cmd in test_commands:
    #     print(f"Команда: '{cmd}' -> Ответ: {run_app(cmd)}")
    print(f"Команда: '{"включи музыку"}' -> Ответ: {run_app("пауза")}")
    # print("\n=== ТЕСТИРОВАНИЕ УТИЛИТ ===")
    # print(f"Время: {get_time()}")
    # # shutdown_pc()
    # print(check_mail())