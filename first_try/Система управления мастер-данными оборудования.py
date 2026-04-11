import pandas as pd
import json
import os
from google.colab import userdata
# Импортируем userdata для безопасного хранения ключей
# Если вы будете использовать этот код вне Colab с .env файлами,
# вам может понадобиться pip install python-dotenv и добавить следующие строки:
# from dotenv import load_dotenv
# load_dotenv() # Загружает переменные из .env файла

# Импортируем библиотеку OpenAI
from openai import OpenAI, APIConnectionError

# --- 1. Настройка API ключей и моделей ---
# Приоритет получения ключей/значений:
# 1. Colab Secrets (для Colab)
# 2. Переменные окружения (для локального запуска с .env файлом или системными переменными)
# 3. Интерактивный запрос через getpass (только для GEMINI_API_KEY, если он нужен)

# Функция для безопасной загрузки переменной
def _load_secret(key_name: str, allow_getpass: bool = False):
    value = None
    # Попытка получить из Colab Secrets (если в Colab)
    try:
        if 'google.colab' in str(get_ipython()): # Проверяем, что мы в Colab
            value = userdata.get(key_name)
            if value:
                print(f"'{key_name}' успешно загружен из Colab Secrets.")
                return value
    except Exception:
        pass # Если не в Colab или ошибка с userdata, переходим к следующему шагу

    # Попытка получить из переменных окружения
    value = os.getenv(key_name)
    if value:
        print(f"'{key_name}' успешно загружен из переменных окружения.")
        return value

    # Если ключ все еще не найден и разрешен getpass
    if allow_getpass:
        print(f"'{key_name}' не найден в Colab Secrets или переменных окружения.")
        print(f"Пожалуйста, введите ваш '{key_name}' вручную.")
        import getpass
        return getpass.getpass(f"Введите ваш {key_name}: ")
    else:
        print(f"Внимание: '{key_name}' не найден. Убедитесь, что он установлен в Colab Secrets или как переменная окружения.")
        return None

# Загрузка GEMINI_API_KEY (пока оставляем загрузку, но он не будет использоваться для анализа)
GEMINI_API_KEY = _load_secret('GEMINI_API_KEY', allow_getpass=False) # allow_getpass=False, так как мы переходим на OpenAI

# Загрузка других переменных
OPENAI_BASE_URL = _load_secret('OPENAI_BASE_URL', allow_getpass=True)
OPENROUTER_API_KEY = _load_secret('OPENROUTER_API_KEY', allow_getpass=True)
LLM_MODEL1 = _load_secret('LLM_MODEL1', allow_getpass=True)
LLM_MODEL2 = _load_secret('LLM_MODEL2', allow_getpass=True)

# --- Инициализация LLM клиента (OpenAI-совместимого) ---
client = None
current_llm_model = None

# Попытка инициализировать OpenAI-совместимый клиент с использованием OpenRouter API Key
if OPENROUTER_API_KEY:
    try:
        client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENAI_BASE_URL if OPENAI_BASE_URL else "https://openrouter.ai/api/v1" # Используем OpenRouter как дефолтный base_url если не указан свой
        )
        # Использование 'gpt-3.5-turbo' для тестирования, чтобы исключить проблемы с конкретной моделью
        current_llm_model = "gpt-3.5-turbo" # Временно устанавливаем на gpt-3.5-turbo
        print(f"Инициализирован OpenAI-совместимый клиент (модель: {current_llm_model}).")
    except Exception as e:
        print(f"Ошибка при инициализации OpenAI-совместимого клиента: {e}")
        client = None
else:
    print("OPENROUTER_API_KEY не найден. Не удалось инициализировать OpenAI-совместимый клиент.")

# Если ни один LLM клиент не инициализирован, выводим ошибку
if not client:
    raise ValueError("Не удалось инициализировать LLM-клиент (OpenAI/OpenRouter). Проверьте API ключи и базовый URL.")

# --- 2. Функция для чтения входящего файла ---
def read_input_file(file_path: str) -> str:
    """
    Читает содержимое текстового файла.
    Поддерживает различные кодировки, пытаясь определить подходящую.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            print(f"Ошибка при чтении файла {file_path}: {e}")
            return ""
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден по пути {file_path}")
        return ""
    except Exception as e:
        print(f"Неизвестная ошибка при чтении файла {file_path}: {e}")
        return ""

# --- 3. Функция для анализа текста с помощью LLM (ранее Gemini) ---
def analyze_content(text_content: str, llm_client: OpenAI, model_name: str) -> dict:
    """
    Отправляет текст в LLM для анализа и извлечения данных.
    Ожидается, что LLM вернет JSON-строку.
    """
    if not text_content:
        return {}

    # Промпт для LLM, просит извлечь специфические данные в формате JSON
    prompt_message = f"""
    Проанализируй следующий текст и извлеки из него следующую информацию:
    'класс' (class), 'подкласс' (subclass), 'модель' (model), и любые другие важные атрибуты или данные,
    которые можно категорировать. Если информация отсутствует, укажите null.
    Представь извлеченную информацию в формате JSON. Например:
    {{
      "класс": "Некий класс",
      "подкласс": "Некий подкласс",
      "модель": "Некая модель",
      "другие_данные": {{
        "атрибут1": "значение1",
        "атрибут2": "значение2"
      }}
    }}

    Текст для анализа:
    ---
    {text_content}
    ---
    """

    try:
        response = llm_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": prompt_message}
            ],
            response_format={"type": "json_object"} # Запрашиваем JSON-объект в ответе
        )
        # Извлекаем контент из ответа OpenAI-подобного клиента
        json_string = response.choices[0].message.content.strip()
        return json.loads(json_string)
    except APIConnectionError as e:
        print(f"Ошибка подключения к API LLM: {e}. Проверьте ваше интернет-соединение, API ключ и базовый URL.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Ошибка декодирования JSON из ответа LLM: {e}")
        print(f"Ответ LLM: {response.choices[0].message.content}")
        return {}
    except Exception as e:
        print(f"Ошибка при взаимодействии с LLM: {e}")
        return {}

# --- 4. Функция для создания и сохранения Excel таблицы ---
def create_and_save_excel(data: list[dict], output_path: str):
    """
    Создает Pandas DataFrame из списка словарей и сохраняет его в Excel файл.
    """
    if not data:
        print("Нет данных для создания Excel файла.")
        return

    # Приведение вложенных словарей к строкам для корректного отображения в Excel
    processed_data = []
    for item in data:
        flat_item = {}
        for key, value in item.items():
            if isinstance(value, dict):
                # Преобразуем вложенный словарь в строку JSON
                flat_item[key] = json.dumps(value, ensure_ascii=False)
            else:
                flat_item[key] = value
        processed_data.append(flat_item)

    df = pd.DataFrame(processed_data)

    try:
        df.to_excel(output_path, index=False)
        print(f"Данные успешно сохранены в {output_path}")
    except Exception as e:
        print(f"Ошибка при сохранении Excel файла {output_path}: {e}")

# --- Основной скрипт ---
# Этот блок предназначен для быстрой проверки и будет убран, так как
# основное приложение использует интерактивный UI для загрузки файлов.
# if __name__ == '__main__':
#     # --- Настройте пути к файлам ---
#     input_file_path = 'path/to/your/input_file.txt'  # Замените на путь к вашему входному файлу
#     output_excel_path = 'output_data.xlsx' # Имя выходного Excel файла

#     # 1. Читаем входящий файл
#     file_content = read_input_file(input_file_path)

#     if file_content:
#         # 2. Анализируем содержимое файла с помощью LLM
#         if client and current_llm_model:
#             extracted_data = analyze_content(file_content, client, current_llm_model)

#             if extracted_data:
#                 # 3. Сохраняем извлеченные данные в Excel
#                 # Оборачиваем extracted_data в список, так как ожидается список словарей
#                 create_and_save_excel([extracted_data], output_excel_path)
#             else:
#                 print("Не удалось извлечь данные из файла с помощью LLM.")
#         else:
#             print("LLM клиент не инициализирован. Проверьте настройки API ключей.")
#     else:
#         print("Не удалось прочитать входной файл.")

# Пример создания фиктивного файла для тестирования (можно удалить после использования)
# with open('path/to/your/input_file.txt', 'w', encoding='utf-8') as f:
#     f.write("""
#     Продукт: Смартфон X100
#     Тип устройства: Мобильный телефон
#     Производитель: TechCorp
#     Модель: X100 Pro
#     Операционная система: Android 13
#     Цвет: Синий
#     Память: 256GB
#     Категория: Электроника
#     Подкатегория: Смартфоны
#     """)
# print("Фиктивный файл 'input_file.txt' создан для тестирования.")
