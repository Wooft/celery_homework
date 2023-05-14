import os
import pathlib
from flask import Flask, request, jsonify, send_file
from flask.views import MethodView
from celery import Celery
from celery.result import AsyncResult
import cv2
from cv2 import dnn_superres

root = pathlib.Path.cwd()
if 'input' not in os.listdir(root):
    os.mkdir('input')
if 'pictures' not in os.listdir(root):
    os.mkdir('pictures')
if 'results' not in os.listdir(root):
    os.mkdir('results')

app = Flask('app')
app.config['UPLOAD_FOLDER'] = os.path.join(root, 'results')
celery = Celery(
    'server',
    backend='redis://localhost:6379/1',
    broker='redis://localhost:6379/2'
)
celery.conf.update(app.config)
class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)

celery.Task = ContextTask

#Функция для быстрой проверки работы Flask
@app.route('/')
def hello_world():
    return 'Hello World'
@celery.task()
def upscale(input_path: str, output_path: str, model_path: str = 'EDSR_x2.pb'):
    """
    :param input_path: путь к изображению для апскейла
    :param output_path:  путь к выходному файлу
    :param model_path: путь к ИИ модели
    :return:
    """

    scaler = dnn_superres.DnnSuperResImpl_create()
    scaler.readModel(model_path)
    scaler.setModel("edsr", 2)
    image = cv2.imread(input_path)
    result = scaler.upsample(image)
    cv2.imwrite(output_path, result)
    file_name = output_path.split('/')[-1]
    return file_name

def get_link(file: str, host: str):
    return f'{host}processed/{file}'

class UpscalerView(MethodView):
    #В инициализации объекта класса происходит проверка на наличие необходимых вспомогательных папок
    def __init__(self):
        self.root = pathlib.Path.cwd()
        self.input = os.path.join(self.root, 'input')
        self.output = os.path.join(self.root, 'results')

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
    def post(self):
        #Получает файл из request и сохраняет его на диск в папку 'input'
        image = request.files['file']
        image.save(os.path.join(self.input, image.filename))
        print(request.host_url)
        #Закидываем файл в upscaler, результат сохраняется в results
        task = upscale.delay(input_path=os.path.join(self.input, image.filename),
                                   output_path=os.path.join(self.output, image.filename))
        return jsonify({
            'task_id': task.id,
            'tasl_status': task.status
        })
@app.route('/processed/<file>', methods=['GET'])
def get_result(file):
    return send_file(path_or_file=os.path.join(app.config['UPLOAD_FOLDER'], file))

app.add_url_rule('/upscale', view_func=UpscalerView.as_view('Upscaler'), methods=['POST'])
app.add_url_rule('/tasks/<task_id>', view_func=UpscalerView.as_view('Task_View'), methods=['GET'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000')
