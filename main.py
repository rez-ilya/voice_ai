import voice
import user_frase_resolver
import sys

def main():
    voice.speak("Голосовой ассистент запущен.")

    while True:
        # 1. Слушаем пользователя
        user_text = voice.listen().lower()

        if user_text:
            print(f"Распознано: {user_text}")

            # 2. Проверяем команду выхода ПЕРЕД обработкой остальных команд
            if "пока" in user_text or "выключись" in user_text:
                final_message = "Голосовой ассистент закончил свою работу. До свидания!"
                voice.speak(final_message)
                print(final_message)
                break  # Выходим из цикла

            # 3. Если это не выход, получаем ответ от резолвера
            response = user_frase_resolver.resolve_intent(user_text)

            # 4. Озвучиваем результат работы команды
            if response:
                voice.speak(response)

    # Завершение работы программы
    print("Программа завершена.")
    sys.exit() # Окончательный выход из процесса

if __name__ == "__main__":
    main()