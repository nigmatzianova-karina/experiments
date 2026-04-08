import google.generativeai as genai
import pandas as pd
import json
import os

# --- 1. Настройка Gemini API ---
# Замените 'YOUR_GEMINI_API_KEY' на ваш фактический API ключ
# Вы можете получить его здесь: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = 'YOUR_GEMINI_API_KEY'
genai.configure(api_key=GEMINI_API_KEY)

# Инициализация модели Gemini
# Используйте подходящую модель, например, 'gemini-pro' для текстовых задач
model = genai.GenerativeModel('gemini-pro')

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

# --- 3. Функция для анализа текста с помощью Gemini ---
def analyze_with_gemini(text_content: str) -> dict:
    """
    Отправляет текст в Gemini для анализа и извлечения данных.
    Ожидается, что Gemini вернет JSON-строку.
    """
    if not text_content:
        return {}

    # Промпт для Gemini, просит извлечь специфические данные в формате JSON
    prompt = f"""
    Проанализируй следующий текст и извлеки из него следующую информацию:
    'класс' (class), 'подкласс' (subclass), 'модель' (model), и любые другие важные атрибуты или данные,
    которые можно категоризировать. Если информация отсутствует, укажите null.
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
        response = model.generate_content(prompt)
        # Попытка извлечь только JSON часть, если есть лишний текст
        json_string = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"Ошибка декодирования JSON из ответа Gemini: {e}")
        print(f"Ответ Gemini: {response.text}")
        return {}
    except Exception as e:
        print(f"Ошибка при взаимодействии с Gemini: {e}")
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
if __name__ == '__main__':
    # --- Настройте пути к файлам ---
    input_file_path = 'path/to/your/input_file.txt'  # Замените на путь к вашему входному файлу
    output_excel_path = 'output_data.xlsx' # Имя выходного Excel файла

    # 1. Читаем входящий файл
    file_content = read_input_file(input_file_path)

    if file_content:
        # 2. Анализируем содержимое файла с помощью Gemini
        extracted_data = analyze_with_gemini(file_content)

        if extracted_data:
            # 3. Сохраняем извлеченные данные в Excel
            # Оборачиваем extracted_data в список, так как ожидается список словарей
            create_and_save_excel([extracted_data], output_excel_path)
        else:
            print("Не удалось извлечь данные из файла с помощью Gemini.")
    else:
        print("Не удалось прочитать входной файл.")

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
