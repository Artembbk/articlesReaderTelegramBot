from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
import subprocess

from typing import List


class Voicer:
    OK_RESPONSE_CODE = 200

    def __init__(self, outputFile, folderId):
        self.outputFile = outputFile
        self.folderId = folderId
        self.iamToken = self.getIamToken()
        self.ssmls = []

    def __call__(self):
        self.createSSMLs()
        print(self.ssmls)
        self.synthesize()

    @staticmethod
    def getIamToken() -> str:
        subprocess.call("./getIam.sh")
        f = open("iam_token")
        iam_token = f.read()
        f.close()
        return iam_token.splitlines()[0]

    def synthesize(self):
        url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
        headers = {"Authorization": "Bearer " + self.iamToken}
        f = open(self.outputFile, "wb")
        f.close()
        for ssml in self.ssmls:
            data = {"ssml": ssml, "lang": "ru-RU", "folderId": self.folderId}
            with requests.post(url, headers=headers, data=data, stream=True) as resp:
                if resp.status_code != self.OK_RESPONSE_CODE:
                    raise RuntimeError(
                        "Invalid response received: code: %d, message: %s"
                        % (resp.status_code, resp.text)
                    )
                with open(self.outputFile, "ab") as f:
                    for audio_content in resp.iter_content(chunk_size=None):
                        f.write(audio_content)

    def createSSMLs(self):
        self.ssmls = []


class MeduzaVoicer(Voicer):
    class NotSupportedPageTypeError(Exception):
        def __init__(self, url, message="page type is not supported"):
            self.url = url
            self.message = message
            super().__init__(self.message)

    # tag's classes, which i want to voice
    QUOTE_CLASS = "QuoteBlock-module_root__2GrcC"
    DESCRIPTION_CLASS = "SimpleBlock-module_lead__35nXx"
    SUB_TITLE_CLASS_H3 = "SimpleBlock-module_h3__2Kv7Y"
    SUB_TITLE_CLASS_H4 = "SimpleBlock-module_h4__2TJO3"
    PARAGRAPH_CLASS = "SimpleBlock-module_p__Q3azD"
    CONTEXT_CLASS = "SimpleBlock-module_context_p__33saY"
    YELLOW_CLASS = "SimpleBlock-module_blockquote__pwpcX"
    SHORT_CLASS = "MediaCaption-module_caption__1hr7Y"
    SLIDE_CLASS = "Slide-slide"
    LIST_CLASS = "ListBlock-module_root__3Q3Ga"
    CARD_CLASS = "CardMaterial-card"
    CARD_TITLE_CLASS = "CardTitle-module_root__1uqqF"
    intrestingClasses = [
        QUOTE_CLASS,
        DESCRIPTION_CLASS,
        SUB_TITLE_CLASS_H3,
        SUB_TITLE_CLASS_H4,
        PARAGRAPH_CLASS,
        CONTEXT_CLASS,
        YELLOW_CLASS,
        LIST_CLASS,
        CARD_CLASS,
        CARD_TITLE_CLASS,
    ]

    # Meduza's page types, which i can handle
    supportedPageTypes = [
        "slides",
        "shapito",
        "feature",
        "news",
        "short",
        "paragraph",
        "episodes",
        "cards",
    ]

    def isSupportedPageType(self) -> bool:
        if len(urlparse(self.url)[2].split("/")) <= 2:
            return False
        return self.pageType in self.supportedPageTypes

    def __init__(self, outputFile, folderId, url):
        Voicer.__init__(self, outputFile, folderId)
        self.url = url
        self.pageType = self.getPageType()
        if not self.isSupportedPageType():
            raise self.NotSupportedPageTypeError(self.url)

    # for example in
    # https://meduza.io/slides/vse-filmy-...
    # page type is 'slides'
    def getPageType(self) -> str:
        dirs = urlparse(self.url)[2].split("/")
        if len(dirs) < 2:
            return ""
        return urlparse(self.url)[2].split("/")[1]

    def isIntrestingTag(self, tag) -> bool:
        if tag.get("class") is None:
            return False
        for class_ in tag.get("class"):
            if class_ in self.intrestingClasses:
                return True
        return False

    def collectTags(self) -> List[str]:
        response = requests.get(self.url)
        soup = BeautifulSoup(response.content, "html.parser")
        if self.pageType == "short":
            tags = [soup("div", self.SHORT_CLASS)[0]]
        elif self.pageType == "slides":
            slides = soup("div", self.SLIDE_CLASS)
            tags = []
            for slide in slides:
                new_tags = [tag for tag in slide.div if self.isIntrestingTag(tag)]
                tags.extend(new_tags)
        elif self.pageType == "cards":
            cards = soup("div", self.CARD_CLASS)
            tags = []
            for card in cards:
                new_tags = [tag for tag in card if self.isIntrestingTag(tag)]
                tags.extend(new_tags)
        else:
            tags = [
                tag
                for tag in soup("div", "GeneralMaterial-article")[0].children
                if self.isIntrestingTag(tag)
            ]
        tags.insert(0, soup.h1)
        return tags

    def createSSMLsFromTags(self, tags):
        ssml = "<speak>"
        for tag in tags:
            if len(ssml) + len(tag.text) + 100 >= 5000:
                ssml += "</speak>"
                self.ssmls.append(ssml)
                ssml = "<speak>"
            if self.QUOTE_CLASS in tag["class"]:
                ssml += "Цитата. "
                ssml += (
                    tag.text.replace("\xa0", " ").replace("<", "(").replace(">", ")")
                )
                ssml += "Конец цитаты"
            elif self.CONTEXT_CLASS in tag["class"]:
                ssml += "<p>"
                ssml += "Контекст. "
                ssml += (
                    tag.text.replace("\xa0", " ").replace("<", "(").replace(">", ")")
                )
                ssml += "</p>"
            elif self.LIST_CLASS in tag["class"]:
                for li in tag("li"):
                    ssml += "<p>"
                    ssml += (
                        li.text.replace("\xa0", " ").replace("<", "(").replace(">", ")")
                    )
                    ssml += "</p>"
            elif self.CARD_TITLE_CLASS in tag["class"]:
                ssml += "<p>"
                ssml += (
                    tag.h3.text.replace("\xa0", " ").replace("<", "(").replace(">", ")")
                )
                ssml += "</p>"
            else:
                ssml += "<p>"
                ssml += (
                    tag.text.replace("\xa0", " ").replace("<", "(").replace(">", ")")
                )
                ssml += "</p>"
        ssml += "</speak>"
        self.ssmls.append(ssml)

    def createSSMLs(self):
        self.createSSMLsFromTags(self.collectTags())
