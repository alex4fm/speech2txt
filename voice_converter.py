import tkinter as tk
from tkinter import ttk, scrolledtext
import speech_recognition as sr
import pyperclip
import pyautogui
import threading
import time
from datetime import datetime
import win32clipboard
import win32con
import win32api
from pywinauto import Application

class VoiceToTextConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Конвертер Голоса в Текст")
        self.root.geometry("600x900")
        self.root.configure(bg='#f0f0f0')
        
        # Переменные состояния
        self.is_listening = False
        self.is_paused = False  # Новое состояние для режима паузы
        self.auto_insert = True  # Автоматическая вставка в активное окно
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Голосовые команды
        self.voice_commands = {
            'поставь на паузу': self.pause_via_voice,
            'пауза': self.pause_via_voice,
            'останови': self.pause_via_voice,
            'начать распознавание': self.resume_via_voice,
            'начать': self.resume_via_voice,
            'продолжить': self.resume_via_voice,
            'старт': self.resume_via_voice
        }
        
        # Настройка микрофона
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Главный контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка весов для растяжения
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Конвертер Голоса в Текст", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Кнопки управления
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, pady=(0, 10), sticky=(tk.W, tk.E))
        
        # Кнопка Старт
        self.start_button = ttk.Button(button_frame, text="Старт", 
                                      command=self.start_listening,
                                      style='Accent.TButton')
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        # Кнопка Пауза
        self.pause_button = ttk.Button(button_frame, text="Пауза", 
                                      command=self.stop_listening,
                                      state='disabled')
        self.pause_button.grid(row=0, column=1, padx=(0, 10))
        
        # Кнопка Очистить
        clear_button = ttk.Button(button_frame, text="Очистить", 
                                 command=self.clear_text)
        clear_button.grid(row=0, column=2, padx=(0, 10))
        
        # Кнопка Копировать
        copy_button = ttk.Button(button_frame, text="Копировать", 
                                command=self.copy_to_clipboard)
        copy_button.grid(row=0, column=3)
        
        # Чекбокс для автоматической вставки
        self.auto_insert_var = tk.BooleanVar(value=True)
        self.auto_insert_checkbox = ttk.Checkbutton(button_frame, 
                                                   text="Автовставка", 
                                                   variable=self.auto_insert_var,
                                                   command=self.toggle_auto_insert)
        self.auto_insert_checkbox.grid(row=0, column=4, padx=(10, 0))
        
        # Область для отображения текста
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        # Текстовое поле
        self.text_area = scrolledtext.ScrolledText(text_frame, 
                                                  wrap=tk.WORD, 
                                                  height=20,
                                                  font=('Arial', 11))
        self.text_area.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Статус
        self.status_label = ttk.Label(main_frame, text="Готов к работе", 
                                     font=('Arial', 10))
        self.status_label.grid(row=3, column=0, pady=(10, 0))
        
        # Счетчик времени
        self.time_label = ttk.Label(main_frame, text="Время: 00:00", 
                                   font=('Arial', 10))
        self.time_label.grid(row=4, column=0, pady=(5, 0))
        
        # Информация о голосовых командах
        commands_frame = ttk.Frame(main_frame)
        commands_frame.grid(row=5, column=0, pady=(10, 0), sticky=(tk.W, tk.E))
        
        commands_label = ttk.Label(commands_frame, 
                                  text="Голосовые команды:", 
                                  font=('Arial', 10, 'bold'))
        commands_label.grid(row=0, column=0, sticky=tk.W)
        
        commands_text = ttk.Label(commands_frame, 
                                 text="'поставь на паузу' / 'начать распознавание'", 
                                 font=('Arial', 9))
        commands_text.grid(row=1, column=0, sticky=tk.W, pady=(2, 0))
        
        # Информация о автовставке
        auto_insert_text = ttk.Label(commands_frame, 
                                    text="Автовставка: текст автоматически вставляется в активное окно", 
                                    font=('Arial', 9))
        auto_insert_text.grid(row=2, column=0, sticky=tk.W, pady=(2, 0))
        
        # Информация об обработке текста
        text_processing_text = ttk.Label(commands_frame, 
                                        text="Обработка: 'запятая'→, 'точка'→. 'новая строка'→↵", 
                                        font=('Arial', 9))
        text_processing_text.grid(row=3, column=0, sticky=tk.W, pady=(2, 0))
        
        # Переменные для отслеживания времени
        self.start_time = None
        self.timer_running = False
        
    def start_listening(self):
        """Начать прослушивание микрофона"""
        if not self.is_listening:
            self.is_listening = True
            self.is_paused = False  # Сбрасываем состояние паузы
            self.start_button.config(state='disabled')
            self.pause_button.config(state='normal')
            self.status_label.config(text="Слушаю... Говорите!")
            
            # Запуск таймера
            self.start_time = time.time()
            self.timer_running = True
            self.update_timer()
            
            # Запуск прослушивания в отдельном потоке
            self.listen_thread = threading.Thread(target=self.listen_loop, daemon=True)
            self.listen_thread.start()
    
    def stop_listening(self):
        """Остановить прослушивание микрофона"""
        if self.is_listening:
            self.is_listening = False
            self.is_paused = False  # Сбрасываем состояние паузы
            self.start_button.config(state='normal')
            self.pause_button.config(state='disabled')
            self.status_label.config(text="Остановлено")
            
            # Остановка таймера
            self.timer_running = False
    
    def listen_loop(self):
        """Основной цикл прослушивания"""
        while self.is_listening:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                
                # Распознавание речи
                try:
                    text = self.recognizer.recognize_google(audio, language='ru-RU')
                    if text.strip():
                        # Проверяем голосовые команды
                        if self.check_voice_command(text):
                            continue  # Пропускаем добавление текста, если это была команда
                        
                        # Если в режиме паузы, не добавляем текст
                        if self.is_paused:
                            continue
                        
                        # Добавляем распознанный текст
                        self.add_text(text)
                        
                        # Автоматическая вставка в активное окно
                        if self.auto_insert:
                            print(f"Попытка вставки текста: '{text}'")
                            
                            # Пробуем Windows API метод (самый надежный)
                            if self.insert_text_windows_api(text):
                                self.status_label.config(text=f"Вставлено (WinAPI): {text[:50]}...")
                                print(f"✅ Текст успешно вставлен (Windows API): '{text}'")
                            else:
                                # Пробуем pywinauto метод
                                print("Пробую pywinauto метод вставки...")
                                if self.insert_text_pywinauto(text):
                                    self.status_label.config(text=f"Вставлено (pywinauto): {text[:50]}...")
                                    print(f"✅ Текст успешно вставлен (pywinauto): '{text}'")
                                else:
                                    # Пробуем основной метод
                                    print("Пробую основной метод вставки...")
                                    if self.insert_text_to_active_window(text):
                                        self.status_label.config(text=f"Вставлено: {text[:50]}...")
                                        print(f"✅ Текст успешно вставлен (основной метод): '{text}'")
                                    else:
                                        # Пробуем альтернативный метод
                                        print("Пробую альтернативный метод вставки...")
                                        if self.insert_text_alternative(text):
                                            self.status_label.config(text=f"Вставлено (альт.): {text[:50]}...")
                                            print(f"✅ Текст успешно вставлен (альтернативный метод): '{text}'")
                                        else:
                                            self.status_label.config(text=f"Ошибка вставки: {text[:50]}...")
                                            print(f"❌ Ошибка при вставке текста: '{text}'")
                        else:
                            # Просто копируем в буфер обмена
                            pyperclip.copy(text)
                            self.status_label.config(text=f"Скопировано: {text[:50]}...")
                            print(f"📋 Текст скопирован в буфер: '{text}'")
                except sr.UnknownValueError:
                    pass  # Не удалось распознать речь
                except sr.RequestError as e:
                    self.status_label.config(text=f"Ошибка распознавания: {e}")
                    
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                self.status_label.config(text=f"Ошибка: {e}")
                break
    
    def add_text(self, text):
        """Добавить текст в область отображения"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_text = f"[{timestamp}] {text}\n"
        
        # Добавление текста в GUI потоке
        self.root.after(0, lambda: self.text_area.insert(tk.END, formatted_text))
        self.root.after(0, lambda: self.text_area.see(tk.END))
    
    def clear_text(self):
        """Очистить текстовую область"""
        self.text_area.delete(1.0, tk.END)
        self.status_label.config(text="Текст очищен")
    
    def copy_to_clipboard(self):
        """Копировать весь текст в буфер обмена"""
        text = self.text_area.get(1.0, tk.END).strip()
        if text:
            pyperclip.copy(text)
            self.status_label.config(text="Текст скопирован в буфер обмена")
        else:
            self.status_label.config(text="Нет текста для копирования")
    
    def update_timer(self):
        """Обновление таймера"""
        if self.timer_running and self.start_time:
            elapsed = time.time() - self.start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.time_label.config(text=f"Время: {minutes:02d}:{seconds:02d}")
            self.root.after(1000, self.update_timer)
    
    def pause_via_voice(self):
        """Пауза через голосовую команду"""
        if self.is_listening and not self.is_paused:
            self.is_paused = True
            self.status_label.config(text="Режим паузы - слушаю команды...")
            self.add_text("[СИСТЕМА] Переключено в режим паузы")
    
    def resume_via_voice(self):
        """Возобновление через голосовую команду"""
        if self.is_listening and self.is_paused:
            self.is_paused = False
            self.status_label.config(text="Слушаю... Говорите!")
            self.add_text("[СИСТЕМА] Распознавание возобновлено")
    
    def check_voice_command(self, text):
        """Проверка голосовых команд"""
        text_lower = text.lower().strip()
        
        for command, func in self.voice_commands.items():
            if command in text_lower:
                # Выполняем команду в GUI потоке
                self.root.after(0, func)
                return True
        return False
    
    def toggle_auto_insert(self):
        """Переключение автоматической вставки"""
        self.auto_insert = self.auto_insert_var.get()
        status = "включена" if self.auto_insert else "отключена"
        self.status_label.config(text=f"Автовставка {status}")
    
    def insert_text_to_active_window(self, text):
        """Вставка текста в активное окно"""
        try:
            # Обрабатываем текст перед вставкой
            processed_text = self.process_text_for_insertion(text)
            
            # Копируем обработанный текст в буфер обмена
            pyperclip.copy(processed_text)
            
            # Увеличиваем задержку для надежности
            time.sleep(0.3)
            
            # Эмулируем Ctrl+V для вставки
            pyautogui.hotkey('ctrl', 'v')
            
            # Дополнительная задержка после вставки
            time.sleep(0.1)
            
            return True
        except Exception as e:
            print(f"Ошибка при вставке текста: {e}")
            return False
    
    def insert_text_alternative(self, text):
        """Альтернативный метод вставки текста"""
        try:
            # Обрабатываем текст перед вставкой
            processed_text = self.process_text_for_insertion(text)
            
            # Копируем обработанный текст в буфер обмена
            pyperclip.copy(processed_text)
            
            # Длинная задержка
            time.sleep(0.5)
            
            # Попробуем альтернативный способ - нажатие клавиш по отдельности
            pyautogui.keyDown('ctrl')
            pyautogui.press('v')
            pyautogui.keyUp('ctrl')
            
            time.sleep(0.2)
            return True
        except Exception as e:
            print(f"Ошибка в альтернативном методе вставки: {e}")
            return False
    
    def process_text_for_insertion(self, text):
        """Обработка текста перед вставкой"""
        processed_text = text
        
        # Заменяем слова на знаки пунктуации
        punctuation_replacements = {
            " запятая": ",",
            "запятая ": ",",
            " запятая ": ",",
            " точка": ".",
            "точка ": ".",
            " точка ": ".",
            " восклицательный знак": "!",
            "восклицательный знак ": "!",
            " восклицательный знак ": "!",
            " вопросительный знак": "?",
            "вопросительный знак ": "?",
            " вопросительный знак ": "?",
            " двоеточие": ":",
            "двоеточие ": ":",
            " двоеточие ": ":",
            " точка с запятой": ";",
            "точка с запятой ": ";",
            " точка с запятой ": ";",
            " тире": " - ",
            "тире ": " - ",
            " тире ": " - ",
            " скобка открывается": "(",
            "скобка открывается ": "(",
            " скобка открывается ": "(",
            " скобка закрывается": ")",
            "скобка закрывается ": ")",
            " скобка закрывается ": ")",
            " кавычка": "\"",
            "кавычка ": "\"",
            " кавычка ": "\"",
            " новая строка": "\n",
            "новая строка ": "\n",
            " новая строка ": "\n"
        }
        
        # Применяем замены
        for word, symbol in punctuation_replacements.items():
            processed_text = processed_text.replace(word, symbol)
        
        # Добавляем пробел в конце, если его нет и текст не заканчивается на знак пунктуации
        if not processed_text.endswith(" ") and not processed_text.endswith(("\n", ".", "!", "?", ":", ";", ")", "\"")):
            processed_text += " "
        
        return processed_text
    
    def insert_text_windows_api(self, text):
        """Вставка текста через Windows API"""
        try:
            # Обрабатываем текст перед вставкой
            processed_text = self.process_text_for_insertion(text)
            
            # Копируем обработанный текст в буфер обмена через Windows API
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(processed_text, win32con.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            
            print(f"Обработанный текст скопирован в буфер через Windows API: '{processed_text}'")
            
            # Задержка
            time.sleep(0.3)
            
            # Эмулируем Ctrl+V через Windows API
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)  # Нажимаем Ctrl
            win32api.keybd_event(ord('V'), 0, 0, 0)  # Нажимаем V
            time.sleep(0.1)
            win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)  # Отпускаем V
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)  # Отпускаем Ctrl
            
            time.sleep(0.2)
            return True
        except Exception as e:
            print(f"Ошибка в Windows API методе вставки: {e}")
            return False
    
    def insert_text_pywinauto(self, text):
        """Вставка текста через pywinauto"""
        try:
            # Обрабатываем текст перед вставкой
            processed_text = self.process_text_for_insertion(text)
            
            # Копируем обработанный текст в буфер обмена
            pyperclip.copy(processed_text)
            
            print(f"Обработанный текст скопирован в буфер через pyperclip: '{processed_text}'")
            
            # Задержка
            time.sleep(0.3)
            
            # Получаем активное окно
            app = Application().connect(active_only=True)
            active_window = app.top_window()
            
            # Фокусируемся на активном окне
            active_window.set_focus()
            time.sleep(0.1)
            
            # Вставляем текст
            active_window.type_keys('^v')
            
            time.sleep(0.2)
            return True
        except Exception as e:
            print(f"Ошибка в pywinauto методе вставки: {e}")
            return False

def main():
    root = tk.Tk()
    app = VoiceToTextConverter(root)
    root.mainloop()

if __name__ == "__main__":
    main() 