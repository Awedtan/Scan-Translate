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


def on_click(x, y, button, pressed):
    print('{0} {1} at {2}'.format(
        button, 'Pressed' if pressed else 'Released', (x, y)))

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
            takeimage(box)
            return False


def takeimage(box):
    im = ImageGrab.grab(box, False, True, None)
    im.save('image.png')


def updateimage(window):
    im = Image.open('image.png').resize(imagesize)
    bio = io.BytesIO()
    im.save(bio, format='png')
    window['image'].update(data=bio.getvalue(), size=imagesize)


def updatetext(window, text):
    window['text'].update(text)


def updategoogle(window, text):
    translator = Translator()
    text = translator.translate(text, dest='en').text
    window['google'].update(text)


def updatedeepl(window, text):
    translator = deepl.Translator(deepl_key.get('key'))
    text = translator.translate_text(text, target_lang='en-us')
    window['deepl'].update(text)


def readimage():
    with io.open('image.png', 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.document_text_detection(
        image=image, image_context=vision.ImageContext())

    fulltext = ''
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            # print('\nBlock confidence: {}\n'.format(block.confidence))
            for paragraph in block.paragraphs:
                # print('Paragraph confidence: {}'.format(paragraph.confidence))
                for word in paragraph.words:
                    word_text = ''.join([
                        symbol.text for symbol in word.symbols
                    ])
                    # print('Word text: {} (confidence: {})'.format(
                    #     word_text, word.confidence))
                    # for symbol in word.symbols:
                    #     print('\tSymbol: {} (confidence: {})'.format(
                    #         symbol.text, symbol.confidence))
                    fulltext = fulltext + word_text + ' '
    pyperclip.copy(fulltext)
    return fulltext


credentials = service_account.Credentials.from_service_account_file(
    'keys.json')
client = vision.ImageAnnotatorClient(credentials=credentials)

f = open('deeplkey.json')
deepl_key = json.load(f)
f.close()

imagesize = (500, 500)

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

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Cancel':
        break
    if event == 'snap':
        with mouse.Listener(on_click=on_click) as listener:
            listener.join()
        text = readimage()
        if (text):
            updateimage(window)
            updatetext(window, text)
            updategoogle(window, text)
            updatedeepl(window, text)
    if event == 'textcopy':
        pyperclip.copy(values['text'])
    if event == 'googlecopy':
        pyperclip.copy(values['google'])
    if event == 'deeplcopy':
        pyperclip.copy(values['deepl'])

window.close()
