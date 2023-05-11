import os
import pathlib

import requests


root = pathlib.Path.cwd()

def main():
    pictures = os.listdir(os.path.join(root, 'pictures'))
    for picture in pictures:
        image = open(os.path.join(root, f'pictures/{picture}'), 'rb')
        file = {'file': image}
        response = requests.post(url='http://127.0.0.1:5000/upscale', files=file)
        print(response.status_code)
        print(response.json())
        break

if __name__ == '__main__':
    main()