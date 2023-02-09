import json
import pathlib
import uuid
import sys
from json import JSONEncoder
import base64

import aircv
import easyocr
import os
from pathlib import Path
import time
from datetime import datetime
import timeit

import flask
import torch
import numpy as np
from PIL import Image, ImageColor, ImageFilter, ImageDraw
from flask import Flask, request
from werkzeug.utils import secure_filename
from PIL import Image
from ComJson import NpEncoder

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
cuda = torch.cuda.is_available()
print('GPU:' + str(cuda))
enEasyocr = easyocr.Reader(['en'])
jpEasyocr = easyocr.Reader(['ja'])
#er = easyocr.Reader(['ja', 'en'], recog_network='custom_example')
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'ocrfiles/'
app.config['UPLOAD_TEMP'] = 'temp/'

def base64_to_utf8(input_str):
    if input_str is not None and len(str(input_str)) > 0:
        return base64.b64decode(input_str).decode('utf-8')
    return ''


def read_textJp(file_stream):
    result = jpEasyocr.readtext(image=file_stream, batch_size=2, min_size=2)
    return json.dumps(result, cls=NpEncoder)

def read_textEn(file_stream):
    result = enEasyocr.readtext(image=file_stream, batch_size=2, min_size=2)
    return json.dumps(result, cls=NpEncoder)

@app.route('/upload', methods=['GET', 'POST'])
def uploader():
    file_bytes = request.stream.read(request.stream.limit)
    imagetext = base64_to_utf8(request.headers["Imagetext"])
    imagefilename = request.headers["Imagefilename"]
    lang = request.headers["Lang"]
    image_w = int(request.headers["Imagew"])
    image_h = int(request.headers["Imageh"])
    txttype = 0
    if len(imagetext) > 0:
        print(imagetext)

        image = Image.frombytes("RGB", (image_w, image_h), file_bytes)
        uuid_str = str(uuid.uuid4())
        # image.save(app.config['UPLOAD_FOLDER'] + uuid_str + '.bmp')
        if len(imagefilename) == 0:
            imagefilename = uuid_str + '.bmp'
        with open(app.config['UPLOAD_FOLDER'] + imagefilename, mode='wb') as f:
            f.write(file_bytes)
        with open(app.config['UPLOAD_FOLDER'] + imagefilename[0:-4] + '.txt', mode='w', encoding='utf-8') as f:
            f.write(imagetext)
        return {"type": 99, "data": ""}
    else:
        if len(imagefilename) == 0:
            txttype = 0
            if lang == "ja":
                text_json = read_textJp(file_bytes)
            elif lang == "en":
                text_json = read_textEn(file_bytes)
        else:
            files = imagefilename.split(",")
            findall = []
            uuid_str = str(uuid.uuid4())
            saveas = os.path.join(app.config['UPLOAD_TEMP'], uuid_str + '.bmp')

            with open(saveas, mode='wb') as f:
                f.write(file_bytes)

            for file in files:
                if len(file) > 0:
                    imgsource = aircv.imread(saveas)
                    imgsearch = aircv.imread(os.path.join(app.config['UPLOAD_FOLDER'],  file))
                    imgdiff = aircv.find_all_template(imgsource, imgsearch, threshold=0.9)
                    findall.append({"filename": file, "data": imgdiff})
            os.remove(saveas)
            text_json = json.dumps(findall, cls=NpEncoder)
            txttype = 1

    return {"type": txttype, "data": text_json}


if __name__ == '__main__':
    enEasyocr.readtext(image='initimage.png', batch_size=2, min_size=2)
    jpEasyocr.readtext(image='initimage.png', batch_size=2, min_size=2)

    app.run()
