import asyncio
import deepl
import googletrans as gt
import io
import json
from PIL import Image, ImageGrab
from pynput import mouse
import pyperclip
import PySimpleGUI as sg
from google.cloud import vision
from google.oauth2 import service_account
#from winsdk.windows.media.ocr import OcrEngine, OcrResult
#from winsdk.windows.globalization import Language
#from winsdk.windows.graphics.imaging import BitmapDecoder
#from winsdk.windows.storage import StorageFile
#from winsdk.windows.foundation import IAsyncOperation, AsyncStatus


# Get Google credentials
credentials = service_account.Credentials.from_service_account_file(
    'keys.json')
client = vision.ImageAnnotatorClient(credentials=credentials)

# Get DeepL credentials
f = open('deeplkey.json')
deepl_key = json.load(f)
f.close()


# Create list of available Windows OCR languages
langs = OcrEngine.available_recognizer_languages
langlist = []
taglist = []
for i in range(0, langs.size):
    langlist.append(langs[i].display_name)
    taglist.append(langs[i].language_tag)

windowslang = taglist[0]

# GUI sizing variables
screensize = (1920, 1080)
imagesize = (500, 500)
rwidth = 8
rheight = 16

# GUI elements
leftcolumn = [[sg.Combo(langlist, default_value=langlist[0], key='selectedlanguage')],
              [sg.Image(size=imagesize, key='image')],
              [sg.Button('Snap', size=(62, 2), key='snap')]]

rightcolumn = [[sg.Text('Raw')],

               [sg.Multiline(size=(rwidth*10, rheight), key='text'),
                sg.Button('Copy', size=(rwidth, rheight), key='textcopy')],

               [sg.Text('Google Translate')],

               [sg.Multiline(size=(rwidth*10, rheight), key='google'),
                sg.Button('Copy', size=(rwidth, rheight), key='googlecopy')],

               [sg.Text('Deepl')],

               [sg.Multiline(size=(rwidth*10, rheight), key='deepl'),
                sg.Button('Copy', size=(rwidth, rheight), key='deeplcopy')]]

layout = [[sg.Column(leftcolumn), sg.Column(rightcolumn)]]

window = sg.Window('Auto Translate', layout,
                   size=(1200, 900), keep_on_top=False)


# Grab image from mouse clicks, save to file
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


# Read image from file, send to OCR method, receive text
async def snap():
    window.disappear()

    # Create "transparent", always-on-top, fullscreen window to allow mouse dragging without affecting other windows
    canvas = sg.Window('fullscreen', layout=[
        []], size=screensize, alpha_channel=0.01, no_titlebar=True, keep_on_top=True, finalize=True)
    canvas.maximize()

    with mouse.Listener(on_click=onclick) as listener:
        listener.join()

    canvas.close()
    window.reappear()

    # Send to Windows OCR
    # file = await StorageFile.get_file_from_path_async('C:\\Users\\danie\\Documents\\Code\\Scan-Translate\\image.png')
    # stream = await file.open_read_async()

    # decoder = await BitmapDecoder.create_async(stream)

    # bitmap = await decoder.get_software_bitmap_async()
    # engine = OcrEngine.try_create_from_language(Language(windowslang))
    # result = await engine.recognize_async(bitmap)

    # text = ''
    # for line in result.lines:
    #     text = text + line.text + '\n'
    # text = text.strip()

    # Send to Google Vision OCR
    image = vision.Image(content=io.open('image.png', 'rb').read())
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
                text = text + '\n'
    text = text.strip()

    if (text):
        pyperclip.copy(text)

        im = Image.open('image.png').resize(imagesize)
        bio = io.BytesIO()
        im.save(bio, 'png')
        window['image'].update(data=bio.getvalue(), size=imagesize)

        window['text'].update(text)

        googletranslate = gt.Translator()
        gtext = googletranslate.translate(text, dest='en').text
        window['google'].update(gtext)

        deepltranslate = deepl.Translator(deepl_key.get('key'))
        dtext = deepltranslate.translate_text(text, target_lang='en-us')
        window['deepl'].update(dtext)


async def main():
    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Cancel':
            break
        if event == 'snap':
            windowslang = taglist[langlist.index(values['selectedlanguage'])]
            await snap()
        if event == 'textcopy':
            pyperclip.copy(values['text'])
        if event == 'googlecopy':
            pyperclip.copy(values['google'])
        if event == 'deeplcopy':
            pyperclip.copy(values['deepl'])
    window.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
