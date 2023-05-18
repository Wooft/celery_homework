FROM python:3.10
COPY . /upscale
#Назначение рабочей директории
WORKDIR /upscale
#Копирование requirements.txt в рабочую директорию
COPY requirements.txt /upscale
#Запуск установки необходимых графических библиотек для работы OpenCV
RUN apt update && apt install ffmpeg libsm6 libxext6  -y
#Запуск установки зависимостей
RUN pip install --no-cache-dir -r /upscale/requirements.txt
ENV PYTHONUNBUFFERED=TRUE
#Запуск приложения Flask через gunicorn
ENTRYPOINT gunicorn server:app --bind 0.0.0.0:5000 --capture-output