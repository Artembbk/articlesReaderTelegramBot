import telebot
from urllib.parse import urlparse
import requests
import validators
from Voicer import MeduzaVoicer

TOKEN = "TOKEN"
outputFile = "audio.opus"
folderId = "folderId"
supportedSites = ["meduza.io"]
OK_RESPONSE_CODE = 200

START_M = """
Привет! Пришли мне ссылку на любую (почти) статью с сайта meduza.io и я верну тебе озвученную версию статьи\n
ВАЖНО!!!\n
Ссылка должна быть ПОЛНОЙ\n
Например такая подойдет: 
https://meduza.io/news/2021/07/16/nayden-propavshiy-pod-tomskom-an-28-on-sovershil-zhestkuyu-posadku-passazhiry-zhivy\n            
А такая нет: 
meduza.io/news/2021/07/16/nayden-propavshiy-pod-tomskom-an-28-on-sovershil-zhestkuyu-posadku-passazhiry-zhivy\n
/help
"""
HELP_M = """
Заходи на сайт meduza.io, выбирай любую (почти) статью и пришли мне ссылку на нее\n
ВАЖНО!!!\n
Ссылка должна быть ПОЛНОЙ\n
Например такая подойдет: 
https://meduza.io/news/2021/07/16/nayden-propavshiy-pod-tomskom-an-28-on-sovershil-zhestkuyu-posadku-passazhiry-zhivy\n
А такая нет: 
meduza.io/news/2021/07/16/nayden-propavshiy-pod-tomskom-an-28-on-sovershil-zhestkuyu-posadku-passazhiry-zhivy\n
/help"""

IS_NOT_URL_M = (
    "Мне нужна полная ссылка, а ты либо прислал не полную, либо вообще что то странное \n"
    "/help"
)

RESPONSE_INVALID_M = (
    "Вроде как ссылка ок, но почему то сайт по ней не отвечает. "
    "Проверь еще раз ссылку или пришли другую. \n"
    "/help"
)

IS_NOT_SUPPORTED_SITE_M = "Я только с сайтом meduza.io работаю.\n" "/help"

IS_NOT_SUPPORTED_PAGE_TYPE = (
    "Да, это сайт meduza.io, но с таким я не умею работать.\n"
    "Либо ты вообще не статью прислал, "
    "либо с таким видом статей я еще не научился работать( \n"
    "/help"
)


UNEXPECTED_ERROR_M = "Что то пошло не так\n" "/help"


def isUrl(url):
    return validators.url(url)


def isValidResponse(url):
    return requests.get(url).status_code == OK_RESPONSE_CODE


def isSupportedSite(url):
    return urlparse(url)[1] in supportedSites


def getSiteName(url):
    return urlparse(url)[1]


class NotSupportedSiteError(Exception):
    def __init__(self, url, message="this site is not supported"):
        self.url = url
        self.message = message
        super().__init__(self.message)


class NotValidResponseError(Exception):
    def __init__(self, url, message="this site is not responding correctly"):
        self.url = url
        self.message = message
        super().__init__(self.message)


class NotUrlError(Exception):
    def __init__(self, url, message="this is not a url"):
        self.url = url
        self.message = message
        super().__init__(self.message)


bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start"])
def send_welcome(m):
    bot.send_message(m.chat.id, START_M)


@bot.message_handler(commands=["help"])
def send_help(m):
    bot.send_message(m.chat.id, HELP_M)


@bot.message_handler(content_types=["text"])
def send_voiced_article(m):
    print("---------------")
    print(m.text)
    try:
        if not isUrl(m.text):
            raise NotUrlError(m.text)
        elif not isSupportedSite(m.text):
            raise NotSupportedSiteError(m.text)
        elif not isValidResponse(m.text):
            raise NotValidResponseError(m.text)
        else:
            if getSiteName(m.text) == "meduza.io":
                bot.send_message(
                    m.chat.id,
                    "Если статья большая, то процесс может затянуться до 5 минут",
                )
                meduza_voicer = MeduzaVoicer(outputFile, folderId, m.text)
                meduza_voicer()
                voice = open("audio.opus", "rb")
                bot.send_voice(m.chat.id, voice)
                print("OK")
    except NotUrlError:
        bot.send_message(m.chat.id, IS_NOT_URL_M)
        print(IS_NOT_URL_M)
    except NotSupportedSiteError:
        bot.send_message(m.chat.id, IS_NOT_SUPPORTED_SITE_M)
        print(IS_NOT_SUPPORTED_SITE_M)
    except NotValidResponseError:
        bot.send_message(m.chat.id, RESPONSE_INVALID_M)
        print(RESPONSE_INVALID_M)
    except MeduzaVoicer.NotSupportedPageTypeError:
        bot.send_message(m.chat.id, IS_NOT_SUPPORTED_PAGE_TYPE)
        print(IS_NOT_SUPPORTED_PAGE_TYPE)
    except Exception as e:
        print(e)
        bot.send_message(m.chat.id, UNEXPECTED_ERROR_M)
        print(UNEXPECTED_ERROR_M)


bot.polling()
