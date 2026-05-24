from gigachat import GigaChat
import config

def ask_ai(question):
    # Библиотека сама сходит за токеном, используя твои credentials
    try:
        # verify_ssl_certs=False критично, так как мы в РФ и работаем со Сбером
        with GigaChat(credentials=config.GIGACHAT_CREDENTIALS, 
                      scope="GIGACHAT_API_PERS", 
                      verify_ssl_certs=False) as giga:
            
            response = giga.chat(f"Ответь очень кратко (1-2 предложения): {question}")
            return response.choices[0].message.content
            
    except Exception as e:
        return f"Ошибка GigaChat: {e}"