import os
import pathlib
import time

import requests


root = pathlib.Path.cwd()

def main():
    pictures = os.listdir(os.path.join(root, 'pictures'))
    list_tasks = []
    files = []

    for picture in pictures:
        image = open(os.path.join(root, f'pictures/{picture}'), 'rb')
        file = {'file': image}
        response = requests.post(url='http://127.0.0.1:5000/upscale', files=file)
        list_tasks.append(response.json().get('task_id'))

    print(list_tasks)

    while len(list_tasks) != 0:
        time.sleep(7)
        for task in list_tasks:
            response = requests.get(url=f'http://127.0.0.1:5000/tasks/{task}')
            print(response.json())
            if response.json().get('task_status') == None:
                files.append(response.json().get('result'))
                list_tasks.remove(task)
                print(task)
                print(list_tasks)
    print(files)

    for file in files:
        response = requests.get(file)
    print(response)
    print(response.content)

if __name__ == '__main__':
    main()