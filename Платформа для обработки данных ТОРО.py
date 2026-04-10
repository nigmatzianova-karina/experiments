import ipywidgets as widgets
from IPython.display import display, HTML
import pandas as pd
import json
import io
import os

# --- Проверка наличия функций из первой ячейки ---
# Убедитесь, что cell_id: 7rCxzD0goc0W был выполнен.

if 'read_input_file' not in globals():
    print("Ошибка: Функция 'read_input_file' не найдена. Пожалуйста, выполните ячейку с ID 7rCxzD0goc0W сначала.")
    raise SystemExit("Прервано: Необходимые функции не определены.")

# Проверка наличия клиента LLM и функции анализа
if 'client' not in globals() or 'analyze_content' not in globals() or 'current_llm_model' not in globals():
    print("Ошибка: LLM клиент ('client'), функция 'analyze_content' или 'current_llm_model' не найдены. Пожалуйста, выполните ячейку с ID 7rCxzD0goc0W сначала.")
    raise SystemExit("Прервано: Необходимые функции LLM не определены.")

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
    accept='.txt, .json, .csv, .xlsx', # Расширяем принимаемые типы файлов
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
        file_extension = os.path.splitext(file_name)[1].lower()

        file_content_for_llm = "" # This will hold the string content for LLM

        try:
            if file_extension == '.xlsx':
                print(f"Обработка Excel файла '{file_name}'...")
                df = pd.read_excel(io.BytesIO(file_content_bytes))
                # Convert DataFrame to a JSON string for LLM to process
                file_content_for_llm = df.to_json(orient='records', force_ascii=False, indent=2)
                print("Excel файл успешно прочитан и преобразован в JSON-строку для анализа.")
            elif file_extension in ['.txt', '.json', '.csv']:
                print(f"Обработка текстового файла '{file_name}'...")
                file_content_for_llm = file_content_bytes.decode('utf-8')
                print(f"Файл '{file_name}' загружен.")
            else:
                print(f"Ошибка: Неподдерживаемый тип файла '{file_extension}'. Поддерживаются .txt, .json, .csv, .xlsx.")
                return

            # Адаптация промпта для более общей иерархии
            # Промпт теперь должен быть более гибким, чтобы принимать как чистый текст, так и JSON-строку
            # analyze_content функция ожидает только текстовое содержимое, промпт формируется внутри неё

            # Используем analyze_content с адаптированным промптом и подготовленным содержимым
            extracted_data = analyze_content(file_content_for_llm, client, current_llm_model)

            if extracted_data:
                print("\n--- Результаты анализа (Таблица) ---")
                # Попытка преобразовать в DataFrame. Может потребоваться более сложная логика
                # для вложенных структур.
                try:
                    if isinstance(extracted_data, list):
                        df = pd.DataFrame(extracted_data)
                    elif isinstance(extracted_data, dict):
                        # If the top level is a dict and contains a list under a key like 'оборудование'
                        # or 'equipment', try to flatten it for DataFrame
                        if 'оборудование' in extracted_data and isinstance(extracted_data['оборудование'], list):
                            df = pd.json_normalize(extracted_data['оборудование'])
                        else:
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
                    if 'df' in locals() and not df.empty: # Если DataFrame был успешно создан и не пуст
                        # Flatten complex columns for CSV if necessary, or keep as JSON string
                        for col in df.columns:
                            if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                                df[col] = df[col].apply(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (dict, list)) else x)
                        df.to_csv(csv_buffer, index=False, encoding='utf-8')
                    else: # Если DataFrame не удалось создать, сохраним raw JSON как одну строку
                        csv_buffer.write(json_output)
                    csv_output = csv_buffer.getvalue()
                except Exception as e:
                    print(f"Ошибка при создании CSV: {e}. Сохраняю как одну JSON-строку.")
                    csv_buffer = io.StringIO()
                    csv_buffer.write(json_output)
                    csv_output = csv_buffer.getvalue()

                # Ensure json_output is a string that can be safely embedded or passed
                json_download_link = f'<a href="data:application/json;charset=utf-8,{json.dumps(json_output)}" download="hierarchy_data.json">Скачать JSON</a>'
                csv_download_link = f'<a href="data:text/csv;charset=utf-8,{csv_output}" download="hierarchy_data.csv">Скачать CSV</a>'

                display(HTML(json_download_link))
                display(HTML(csv_download_link))

            else:
                print("Не удалось извлечь данные из файла с помощью LLM. Проверьте содержимое файла и промпт.")
        except pd.errors.EmptyDataError:
            print(f"Ошибка: Файл '{file_name}' пуст или не содержит данных.")
        except pd.errors.ParserError as pe:
            print(f"Ошибка парсинга Excel файла '{file_name}': {pe}. Убедитесь, что файл имеет корректный формат.")
        except UnicodeDecodeError:
            print(f"Ошибка: Не удалось декодировать текстовый файл '{file_name}' как UTF-8. Попробуйте другую кодировку или убедитесь, что файл текстовый.")
        except Exception as e:
            print(f"Произошла ошибка при обработке файла иерархии: {e}")

hierarchy_analyze_button.on_click(on_hierarchy_analyze_button_clicked)

# --- 2. Вкладка "Правила нормализации НСИ" ---
norm_rules_uploader = widgets.FileUpload(
    accept='.txt, .json, .csv, .xlsx',
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
        file_extension = os.path.splitext(file_name)[1].lower()

        try:
            if file_extension == '.xlsx':
                print(f"Обработка Excel файла '{file_name}'...")
                df = pd.read_excel(io.BytesIO(file_content_bytes))
                print("\n--- Содержимое файла правил нормализации НСИ (первые 5 строк) ---")
                display(df.head())
            elif file_extension in ['.txt', '.json', '.csv']:
                file_content = file_content_bytes.decode('utf-8')
                print(f"Файл '{file_name}' загружен.")
                print("\n--- Содержимое файла правил нормализации НСИ ---")
                print(file_content)
            else:
                print(f"Ошибка: Неподдерживаемый тип файла '{file_extension}'. Поддерживаются .txt, .json, .csv, .xlsx.")
                return

        except pd.errors.EmptyDataError:
            print(f"Ошибка: Файл '{file_name}' пуст или не содержит данных.")
        except pd.errors.ParserError as pe:
            print(f"Ошибка парсинга Excel файла '{file_name}': {pe}. Убедитесь, что файл имеет корректный формат.")
        except UnicodeDecodeError:
            print(f"Ошибка: Не удалось декодировать текстовый файл '{file_name}' как UTF-8.")
        except Exception as e:
            print(f"Произошла ошибка при обработке файла правил нормализации: {e}")

norm_rules_display_button.on_click(on_norm_rules_display_button_clicked)


# --- 3. Вкладка "Классификатор оборудования" ---
classifier_uploader = widgets.FileUpload(
    accept='.txt, .json, .csv, .xlsx',
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
        file_extension = os.path.splitext(file_name)[1].lower()

        try:
            if file_extension == '.xlsx':
                print(f"Обработка Excel файла '{file_name}'...")
                df = pd.read_excel(io.BytesIO(file_content_bytes))
                print("\n--- Содержимое файла классификатора оборудования (первые 5 строк) ---")
                display(df.head())
            elif file_extension in ['.txt', '.json', '.csv']:
                file_content = file_content_bytes.decode('utf-8')
                print(f"Файл '{file_name}' загружен.")
                print("\n--- Содержимое файла классификатора оборудования ---")
                print(file_content)
            else:
                print(f"Ошибка: Неподдерживаемый тип файла '{file_extension}'. Поддерживаются .txt, .json, .csv, .xlsx.")
                return

        except pd.errors.EmptyDataError:
            print(f"Ошибка: Файл '{file_name}' пуст или не содержит данных.")
        except pd.errors.ParserError as pe:
            print(f"Ошибка парсинга Excel файла '{file_name}': {pe}. Убедитесь, что файл имеет корректный формат.")
        except UnicodeDecodeError:
            print(f"Ошибка: Не удалось декодировать текстовый файл '{file_name}' как UTF-8.")
        except Exception as e:
            print(f"Произошла ошибка при обработке файла классификатора: {e}")

classifier_display_button.on_click(on_classifier_display_button_clicked)


# --- 4. Вкладка "Управление моделями" (Placeholder) ---
models_tab_content = widgets.VBox([
    widgets.HTML("<h3>Управление справочником моделей</h3>"),
    widgets.HTML("<p>Здесь будет функционал для загрузки, ручного создания, отображения и нормализации моделей.</p>"),
    widgets.HTML("""<p><b>Ожидаемые функции:</b></p><ul>
        <li>Загрузка справочника моделей (CSV/JSON).</li>
        <li>Ручное создание/редактирование моделей.</li>
        <li>Нормализация моделей по правилам НСИ.</li>
        <li>Отображение нормализованных моделей.</li>
        <li>Сохранение справочника моделей.</li>
    </ul>""")
])

# --- 5. Вкладка "Классификация" (Placeholder) ---
classification_tab_content = widgets.VBox([
    widgets.HTML("<h3>Классификация моделей оборудования</h3>"),
    widgets.HTML("<p>Здесь будет функционал для классификации моделей на основе загруженного классификатора.</p>"),
    widgets.HTML("""<p><b>Ожидаемые функции:</b></p><ul>
        <li>Классификация моделей на основании классификатора.</li>
        <li>Классификация неопознанных моделей.</li>
        <li>Отображение результатов классификации.</li>
        <li>Сохранение классифицированных моделей.</li>
    </ul>""")
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
