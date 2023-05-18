import os
from os import getenv
import pathlib
from flask import Flask, request, jsonify, send_file
from flask.views import MethodView
from celery import Celery
from celery.result import AsyncResult
import cv2
from cv2 import dnn_superres
from errors import HttpError
from decouple import config

#Получение абсолютного пути к папке проекта
root = pathlib.Path.cwd()
#Проверка и создание необходимых папок для работы проекта
if config('INPUT_FOLDER') not in os.listdir(root):
    os.mkdir(config('INPUT_FOLDER'))
if config('TEST_FOLDER') not in os.listdir(root):
    os.mkdir(config('TEST_FOLDER'))
if config('OUTPUT_FOLDER') not in os.listdir(root):
    os.mkdir(config('OUTPUT_FOLDER'))

#Создание эксземпляра класса DnnSuperRes
scaler = dnn_superres.DnnSuperResImpl_create()
scaler.readModel(config('UPSCALE_MODEL'))
scaler.setModel("edsr", 2)

#Создание приложения (экземпляра класса) Flask
app = Flask('app')
app.config['UPLOAD_FOLDER'] = os.path.join(root, 'results')
#Создание экземпляра класса Celery
celery = Celery(
    'server',
    backend='redis://redis:6379/1',
    broker='redis://redis:6379/2'
)
celery.conf.update(app.config)
#Переопределение метода ContextTask
class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)

celery.Task = ContextTask
#Функция обработки ошибок
@app.errorhandler(HttpError)
def error_handler(error: AttributeError):
    http_responce = jsonify({
        'status': 'error',
        'description': error.message
    })
    http_responce.status_code = error.status_code
    return http_responce

#Функция для вывода домашней страниы Flask
@app.route('/')
def hello_world():
    return 'Hello World'

#Функция обработаки изображений
@celery.task()
def upscale(input_path: str, output_path: str):
    """
    :param input_path: путь к изображению для апскейла
    :param output_path:  путь к выходному файлу
    :param model_path: путь к ИИ модели
    :return:
    """

    image = cv2.imread(input_path)
    result = scaler.upsample(image)
    cv2.imwrite(output_path, result)
    file_name = output_path.split('/')[-1]
    return file_name

#Функция дл получения ссылки на файл
def get_link(file: str, host: str):
    return f'{host}processed/{file}'

#Основной класс для работы с запросами на обработку изображений и получения статуса
class UpscalerView(MethodView):
    #В инициализации объекта класса происходит проверка на наличие необходимых вспомогательных папок
    def __init__(self):
        self.root = pathlib.Path.cwd()
        self.input = os.path.join(self.root, config('INPUT_FOLDER'))
        self.output = os.path.join(self.root, config('OUTPUT_FOLDER'))

#Возвращает статус выполнения задачи Celery
    def get(self, task_id):
        task = AsyncResult(task_id, app=celery)
        if task.status == 'PENDING':
            return jsonify({
                'task_status': task.status
            })
        if task.status == 'SUCCESS':
            return jsonify({
                'result': get_link(file=task.result, host=request.host_url)
            })
        if task.status == 'FAILURE':
            raise HttpError(status_code=409, message={
                'status': 'error',
                'description': 'Failure image processing'
            })
    #Принимает изображение и запускает задачу в Celery по его апскейлингу
    def post(self):
        #Получает файл из request и сохраняет его на диск в папку 'input'
        image = request.files.get('file')
        if image == None:
            raise HttpError(status_code=409, message='File not found')
        try:
            image.save(os.path.join(self.input, image.filename))
        except AttributeError:
            raise HttpError(status_code=409)
        #Закидываем файл в upscaler, результат сохраняется в results
        task = upscale.delay(input_path=os.path.join(self.input, image.filename),
                                           output_path=os.path.join(self.output, image.filename))
        return jsonify({
            'task_id': task.id,
            'tasl_status': task.status
        })
#Возвращает ссылку на результат
@app.route('/processed/<file>', methods=['GET'])
def get_result(file):
    return send_file(path_or_file=os.path.join(app.config['UPLOAD_FOLDER'], file))

app.add_url_rule('/upscale', view_func=UpscalerView.as_view('Upscaler'), methods=['POST'])
app.add_url_rule('/tasks/<task_id>', view_func=UpscalerView.as_view('Task_View'), methods=['GET'])
