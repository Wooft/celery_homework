import os
import pathlib
from upscale import upscale
from flask import Flask, request, jsonify, send_file
from flask.views import MethodView
from celery import Celery
from celery.result import AsyncResult

celery = Celery(
    'app',
    backend='redis://localhost:6379/1',
    broker='redis://localhost:6379/2'
)

app = Flask('upscaler')
#Функция для быстрой проверки работы Flask
@app.route('/')
def hello_world():
    return 'Hello World'
@celery.task
def upscale_image(input_path, output_path):
    result = upscale(input_path=input_path, output_path=output_path)
    return result

class UpscalerView(MethodView):
    #В инициализации объекта класса происходит проверка на наличие необходимых вспомогательных папок
    def __init__(self):
        self.root = pathlib.Path.cwd()
        if 'input' not in os.listdir(self.root):
            os.mkdir('input')
        elif 'pictures' not in os.listdir(self.root):
            os.mkdir('pictures')
        elif 'results' not in os.listdir(self.root):
            os.mkdir('results')
        self.input = os.path.join(self.root, 'input')
        self.output = os.path.join(self.root, 'results')

    def get(self, task_id):
        task = AsyncResult(task_id, app=celery)
        return jsonify({
            'task_id': task.id,
            'task_status': task.status
        })
    def post(self):
        #Получает файл из request и сохраняет его на диск в папку 'input'
        image = request.files['file']
        image.save(os.path.join(self.input, image.filename))
        #Закидываем файл в upscaler, результат сохраняется в results
        task = upscale_image.delay(input_path=os.path.join(self.input, image.filename),
                                   output_path=os.path.join(self.output, image.filename))
        # result = upscale(input_path=os.path.join(self.input, image.filename), output_path=os.path.join(self.output, image.filename))
        return jsonify({
            'task_id': task.id,
            'tasl_status': task.status
        })


app.add_url_rule('/upscale', view_func=UpscalerView.as_view('Upscaler'), methods=['POST'])

if __name__ == '__main__':
    app.run()
