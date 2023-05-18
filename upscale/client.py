import os
import pathlib
import time
from decouple import config
import requests


root = pathlib.Path.cwd()

def main():
    pictures = os.listdir(os.path.join(root, config('TEST_FOLDER')))
    list_tasks = []
    files = []

    for picture in pictures:
        image = open(os.path.join(root, f'pictures/{picture}'), 'rb')
        file = {'file': image}
        response = requests.post(url='http://0.0.0.0:5000/upscale', files=file)
        list_tasks.append(response.json().get('task_id'))

    print(list_tasks)

    while len(list_tasks) != 0:
        time.sleep(7)
        for task in list_tasks:
            response = requests.get(url=f'http://0.0.0.0:5000/tasks/{task}')
            print(response.json())
            if response.json().get('task_status') == None:
                files.append(response.json().get('result'))
                list_tasks.remove(task)
                print(task)
                print(list_tasks)
    print(files)

    # for file in files:
    #     response = requests.get(file)
    # print(response)
    # print(response.content)
    #
    # response = requests.post('http://127.0.0.1:5000/upscale')
    # print(response.status_code)
    # print(response.json())

    # image = open(os.path.join(root, f'pictures/123.odt'), 'rb')
    # file = {'file': image}
    # response = requests.post('http://127.0.0.1:5000/upscale', files=file)
    # print(response.status_code)
    # print(response.json())
    # task = response.json().get('task_id')
    #
    # response = requests.get(url=f'http://127.0.0.1:5000/tasks/{task}')
    # print(response.status_code)
    # print(response.json())



if __name__ == '__main__':
    main()