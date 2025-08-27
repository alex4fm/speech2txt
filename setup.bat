@echo off
echo Быстрая установка окружения...

REM Создание виртуального окружения
python -m venv venv || (echo Ошибка создания venv && pause && exit /b 1)

REM Активация окружения
call venv\Scripts\activate.bat

REM Установка зависимостей
pip install -r requirements.txt

echo Установка завершена!
pause