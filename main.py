import io
import json
import deepl
import pyperclip
import PySimpleGUI as sg
from PIL import Image, ImageGrab
from pynput import mouse
from google.cloud import vision
from google.oauth2 import service_account
from googletrans import Translator


credentials = service_account.Credentials.from_service_account_file(
    'keys.json')
client = vision.ImageAnnotatorClient(credentials=credentials)

f = open('deeplkey.json')
deepl_key = json.load(f)
f.close()

imagesize = (500, 500)
screensize = (1920, 1080)

leftcolumn = [[sg.Image(size=imagesize, key='image')],
              [sg.Button('Snap', size=(62, 2), key='snap')],
              [sg.Multiline(size=(70, 16), key='text')],
              [sg.Button('Copy', size=(62, 2), key='textcopy')]]

rightcolumn = [[sg.Text('Google Translate')],
               [sg.Multiline(size=(80, 18), key='google'), sg.Button(
                   'Copy', size=(8, 18), key='googlecopy')],
               [sg.Text('Deepl')],
               [sg.Multiline(size=(80, 18), key='deepl'), sg.Button('Copy', size=(8, 18), key='deeplcopy')]]

layout = [[sg.Column(leftcolumn), sg.Column(rightcolumn)]]

window = sg.Window('Auto Translate', layout,
                   size=(1200, 900), keep_on_top=False)


def onclick(x, y, button, pressed):
    # print('{0} {1} at {2}'.format(
    #     button, 'Pressed' if pressed else 'Released', (x, y)))
    if (button == mouse.Button.left):
        if (pressed):
            global left, top
            left = x
            top = y
        else:
            global right, bottom
            right = x
            bottom = y
            box = (min(left, right), min(top, bottom),
                   max(left, right), max(top, bottom))

            ImageGrab.grab(box, False, True, None).save('image.png')
            return False


def snap():
    window.disappear()

    canvas = sg.Window('fullscreen', layout=[
        []], size=screensize, alpha_channel=0.01, no_titlebar=True, keep_on_top=True, finalize=True)
    canvas.maximize()
    with mouse.Listener(on_click=onclick) as listener:
        listener.join()

    canvas.close()
    window.reappear()

    content = io.open('image.png', 'rb').read()
    image = vision.Image(content=content)
    response = client.document_text_detection(
        image=image, image_context=vision.ImageContext())

    text = ''
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    word_text = ''.join([
                        symbol.text for symbol in word.symbols
                    ])
                    text = text + word_text + ' '

    if (text):
        pyperclip.copy(text)

        im = Image.open('image.png').resize(imagesize)
        bio = io.BytesIO()
        im.save(bio, 'png')
        window['image'].update(data=bio.getvalue(), size=imagesize)

        window['text'].update(text)

        googletranslate = Translator()
        text = googletranslate.translate(text, dest='en').text
        window['google'].update(text)

        deepltranslate = deepl.Translator(deepl_key.get('key'))
        text = deepltranslate.translate_text(text, target_lang='en-us')
        window['deepl'].update(text)


while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Cancel':
        break
    if event == 'snap':
        snap()
    if event == 'textcopy':
        pyperclip.copy(values['text'])
    if event == 'googlecopy':
        pyperclip.copy(values['google'])
    if event == 'deeplcopy':
        pyperclip.copy(values['deepl'])

window.close()
