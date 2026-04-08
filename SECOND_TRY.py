"""
ПРОМТ

сделай код с формой для загрузки, и отображения иерархии в виде таблицы и дерева с функцией сохраниения результат в json,
csv окно предназначеное для загрузки правил нормализации, классификации и обработке моделей оборудования. в данном окне реализована 
загрузка документауции на типовой объект ремонта(тор). типовой объект ремонта это модель с предопределенным классом\ поклассом для нее
в формате сцепки модель+класс+подкласс=модель/класс/подкласс(тор) входная информация:
1. иерархия оборудования
2. правила нормализации НСИ
3.Классификатор оборудования "классы/подклассы" 

Функции:
1. Загрузка правил нормализации НСИ
2. Отображение иерархии оборудования из загруженного файла 
3. Корректировка иерархии оборудования
4. Ведение справочника моделей
5. Загрузка справочника моделей
6. Ручное создание справочника моделей
7. Нормализация моделей по правилам НСИ и внесение результата в отдельное поле
8. Ведение справочника классификатора оборудования
9. Загрузка справочника классификатора оборудования 
10. Классификация моделей на основании классификатора
11. Классификация неопознанных моделей оборудования (на пустые позиции из п.10) 
12. Ручная корректировка правил нормализации в системе.
"""



import ipywidgets as widgets
from IPython.display import display, HTML
import pandas as pd
import json
import io
import os

# --- Проверка наличия функций из первой ячейки ---
# Убедитесь, что cell_id: 7rCxzD0goc0W был выполнен.
# Если 'read_input_file' или 'analyze_with_gemini' не определены, вы получите ошибку.

if 'read_input_file' not in globals():
    print("Ошибка: Функция 'read_input_file' не найдена. Пожалуйста, выполните ячейку с ID 7rCxzD0goc0W сначала.")
    raise SystemExit("Прервано: Необходимые функции не определены.")

if 'analyze_with_gemini' not in globals():
    print("Ошибка: Функция 'analyze_with_gemini' не найдена. Пожалуйста, выполните ячейку с ID 7rCxzD0goc0W сначала.")
    raise SystemExit("Прервано: Необходимые функции не определены.")

# --- Вспомогательная функция для отображения данных в виде дерева (простое текстовое представление) ---
def display_as_tree(data, indent=0):
    tree_str = ""
    if isinstance(data, dict):
        for key, value in data.items():
            tree_str += '  ' * indent + f"- {key}: "
            if isinstance(value, (dict, list)) and value:
                tree_str += "\n" + display_as_tree(value, indent + 1)
            else:
                tree_str += str(value) + "\n"
    elif isinstance(data, list):
        for item in data:
            tree_str += '  ' * indent + "- "
            if isinstance(item, (dict, list)) and item:
                tree_str += "\n" + display_as_tree(item, indent + 1)
            else:
                tree_str += str(item) + "\n"
    return tree_str

# --- UI Элементы для каждой вкладки ---

# --- 1. Вкладка "Иерархия оборудования" ---
hierarchy_uploader = widgets.FileUpload(
    accept='.txt, .json, .csv', # Расширяем принимаемые типы файлов
    multiple=False,
    description='Загрузить иерархию оборудования'
)
hierarchy_analyze_button = widgets.Button(description='Анализировать и отобразить иерархию')
hierarchy_output_area = widgets.Output()

def on_hierarchy_analyze_button_clicked(b):
    with hierarchy_output_area:
        hierarchy_output_area.clear_output()
        if not hierarchy_uploader.value:
            print("Пожалуйста, загрузите файл иерархии оборудования.")
            return

        uploaded_file = list(hierarchy_uploader.value.values())[0]
        file_name = uploaded_file['metadata']['name']
        file_content_bytes = uploaded_file['content']

        try:
            file_content = file_content_bytes.decode('utf-8')
            print(f"Файл '{file_name}' загружен.")

            # Адаптация промпта Gemini для более общей иерархии
            # Вы можете изменить этот промпт для каждого типа данных
            gemini_prompt_hierarchy = f"""
            Проанализируй следующий текст, который описывает иерархию оборудования. 
            Извлеки все уровни иерархии, включая родительские-дочерние отношения, 
            атрибуты каждого элемента (например, модель, класс, подкласс, производитель и т.д.).
            Представь извлеченную информацию в формате JSON, где каждый элемент иерархии 
            является объектом с его атрибутами и, возможно, вложенным списком дочерних элементов.
            Если информация отсутствует, укажите null. 
            Если текст представляет собой плоский список, преобразовать его в иерархию, если это возможно, 
            основываясь на логике отношений. Например:
            {{
              "оборудование": [
                {{
                  "название": "Машина А",
                  "тип": "Производственная",
                  "компоненты": [
                    {{
                      "название": "Двигатель 1",
                      "модель": "XYZ-100",
                      "класс": "Механизм"
                    }},
                    {{
                      "название": "Панель управления",
                      "класс": "Электроника"
                    }}
                  ]
                }},
                {{
                  "название": "Машина Б",
                  "тип": "Упаковочная"
                }}
              ]
            }}
            
            Текст для анализа:
            ---
            {file_content}
            ---
            """

            # Временное изменение prompt для analyze_with_gemini, если это возможно,
            # или создание новой специализированной функции
            # Для простоты, пока будем использовать analyze_with_gemini с текущим промптом
            # и ожидать, что пользователь адаптирует prompt в первой ячейке или создаст новую функцию.
            # TODO: Для более сложных сценариев, рассмотреть создание `analyze_hierarchy_with_gemini`
            extracted_data = analyze_with_gemini(file_content)

            if extracted_data:
                print("\n--- Результаты анализа (Таблица) ---")
                # Попытка преобразовать в DataFrame. Может потребоваться более сложная логика
                # для вложенных структур.
                try:
                    if isinstance(extracted_data, list):
                        df = pd.DataFrame(extracted_data)
                    elif isinstance(extracted_data, dict):
                        df = pd.DataFrame([extracted_data])
                    else:
                        df = pd.DataFrame({'Data': [str(extracted_data)]})
                    display(df)
                except Exception as e:
                    print(f"Ошибка при создании DataFrame: {e}")
                    display(pd.DataFrame({'Raw Data': [str(extracted_data)]}))

                print("\n--- Результаты анализа (Иерархическое представление) ---")
                # Простое текстовое представление дерева
                print(display_as_tree(extracted_data))

                # --- Функции сохранения ---
                print("\n--- Опции сохранения ---")
                json_output = json.dumps(extracted_data, ensure_ascii=False, indent=2)
                
                csv_buffer = io.StringIO()
                # Для вложенных данных pandas to_csv может быть сложным, 
                # потребуется "разворачивать" JSON перед сохранением в CSV
                try:
                    if 'df' in locals(): # Если DataFrame был успешно создан
                        df.to_csv(csv_buffer, index=False, encoding='utf-8')
                    else: # Если DataFrame не удалось создать, сохраним raw JSON как одну строку
                        csv_buffer.write(json_output)
                    csv_output = csv_buffer.getvalue()
                except Exception as e:
                    print(f"Ошибка при создании CSV: {e}. Сохраняю как одну JSON-строку.")
                    csv_buffer = io.StringIO()
                    csv_buffer.write(json_output)
                    csv_output = csv_buffer.getvalue()

                json_download_link = f'<a href="data:application/json;charset=utf-8,{json.dumps(json_output)}" download="hierarchy_data.json">Скачать JSON</a>'
                csv_download_link = f'<a href="data:text/csv;charset=utf-8,{csv_output}" download="hierarchy_data.csv">Скачать CSV</a>'

                display(HTML(json_download_link))
                display(HTML(csv_download_link))

            else:
                print("Не удалось извлечь данные из файла с помощью Gemini. Проверьте содержимое файла и промпт.")
        except UnicodeDecodeError:
            print(f"Ошибка: Не удалось декодировать файл '{file_name}' как UTF-8. Попробуйте другую кодировку или убедитесь, что файл текстовый.")
        except Exception as e:
            print(f"Произошла ошибка при обработке файла иерархии: {e}")

hierarchy_analyze_button.on_click(on_hierarchy_analyze_button_clicked)

# --- 2. Вкладка "Правила нормализации НСИ" ---
norm_rules_uploader = widgets.FileUpload(
    accept='.txt, .json, .csv', 
    multiple=False,
    description='Загрузить правила нормализации НСИ'
)
norm_rules_display_button = widgets.Button(description='Отобразить правила')
norm_rules_output_area = widgets.Output()

def on_norm_rules_display_button_clicked(b):
    with norm_rules_output_area:
        norm_rules_output_area.clear_output()
        if not norm_rules_uploader.value:
            print("Пожалуйста, загрузите файл правил нормализации.")
            return

        uploaded_file = list(norm_rules_uploader.value.values())[0]
        file_name = uploaded_file['metadata']['name']
        file_content_bytes = uploaded_file['content']
        
        try:
            file_content = file_content_bytes.decode('utf-8')
            print(f"Файл '{file_name}' загружен.")
            print("\n--- Содержимое файла правил нормализации НСИ ---")
            print(file_content) # Просто отображаем содержимое

            # TODO: Здесь можно добавить парсинг и структурированное отображение правил
            # Например, если правила в JSON, можно их распарсить и отобразить как DataFrame

            # Кнопка для ручной корректировки (Placeholder)
            # manual_edit_button = widgets.Button(description='Ручная корректировка правил')
            # display(manual_edit_button)

        except UnicodeDecodeError:
            print(f"Ошибка: Не удалось декодировать файл '{file_name}' как UTF-8.")
        except Exception as e:
            print(f"Произошла ошибка при обработке файла правил нормализации: {e}")

norm_rules_display_button.on_click(on_norm_rules_display_button_clicked)


# --- 3. Вкладка "Классификатор оборудования" ---
classifier_uploader = widgets.FileUpload(
    accept='.txt, .json, .csv', 
    multiple=False,
    description='Загрузить классификатор оборудования'
)
classifier_display_button = widgets.Button(description='Отобразить классификатор')
classifier_output_area = widgets.Output()

def on_classifier_display_button_clicked(b):
    with classifier_output_area:
        classifier_output_area.clear_output()
        if not classifier_uploader.value:
            print("Пожалуйста, загрузите файл классификатора оборудования.")
            return

        uploaded_file = list(classifier_uploader.value.values())[0]
        file_name = uploaded_file['metadata']['name']
        file_content_bytes = uploaded_file['content']

        try:
            file_content = file_content_bytes.decode('utf-8')
            print(f"Файл '{file_name}' загружен.")
            print("\n--- Содержимое файла классификатора оборудования ---")
            print(file_content) # Просто отображаем содержимое

            # TODO: Здесь можно добавить парсинг и структурированное отображение классификатора

        except UnicodeDecodeError:
            print(f"Ошибка: Не удалось декодировать файл '{file_name}' как UTF-8.")
        except Exception as e:
            print(f"Произошла ошибка при обработке файла классификатора: {e}")

classifier_display_button.on_click(on_classifier_display_button_clicked)


# --- 4. Вкладка "Управление моделями" (Placeholder) ---
models_tab_content = widgets.VBox([
    widgets.HTML("<h3>Управление справочником моделей</h3>"),
    widgets.HTML("<p>Здесь будет функционал для загрузки, ручного создания, отображения и нормализации моделей.</p>"),
    widgets.HTML("<p><b>Ожидаемые функции:</b></p><ul>
        <li>Загрузка справочника моделей (CSV/JSON).</li>
        <li>Ручное создание/редактирование моделей.</li>
        <li>Нормализация моделей по правилам НСИ.</li>
        <li>Отображение нормализованных моделей.</li>
        <li>Сохранение справочника моделей.</li>
    </ul>")
])

# --- 5. Вкладка "Классификация" (Placeholder) ---
classification_tab_content = widgets.VBox([
    widgets.HTML("<h3>Классификация моделей оборудования</h3>"),
    widgets.HTML("<p>Здесь будет функционал для классификации моделей на основе загруженного классификатора.</p>"),
    widgets.HTML("<p><b>Ожидаемые функции:</b></p><ul>
        <li>Классификация моделей на основании классификатора.</li>
        <li>Классификация неопознанных моделей.</li>
        <li>Отображение результатов классификации.</li>
        <li>Сохранение классифицированных моделей.</li>
    </ul>")
])


# --- Создание вкладок ---
tabs = widgets.Tab()
tabs.children = [
    widgets.VBox([hierarchy_uploader, hierarchy_analyze_button, hierarchy_output_area]),
    widgets.VBox([norm_rules_uploader, norm_rules_display_button, norm_rules_output_area]),
    widgets.VBox([classifier_uploader, classifier_display_button, classifier_output_area]),
    models_tab_content,
    classification_tab_content
]

tabs.set_title(0, 'Иерархия оборудования')
tabs.set_title(1, 'Правила нормализации НСИ')
tabs.set_title(2, 'Классификатор оборудования')
tabs.set_title(3, 'Управление моделями')
tabs.set_title(4, 'Классификация')

display(tabs)
