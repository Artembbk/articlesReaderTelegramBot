# articlesReaderTelegramBot
Телеграм бот, который получает на вход ссылку с определнных сайтов (на данный момент только с meduza.io) и возращает в виде голосового сообщения озвученный текст статьи.

Часто бывает такое, что читать статьи с любимого сайта неудобно. Например, находясь в дороге гораздо проще прослушать эту статью. Именно для этого и нужен этот бот.

Для сбора текста используется BeautifulSoup4. Для озвучивания используется Yandex SpeechKit. Сам бот написан с помощью pyTelegramBotAPI

Также в прогрмамме используются библиотеки subprocess, urlparse, requests, validators

Для использования SpeechKit необходимо:

1) На [странице биллинга](https://console.cloud.yandex.ru/billing) убедитесь, что платежный аккаунт находится в статусе ACTIVE или TRIAL_ACTIVE. Если платежного аккаунта нет, [создайте его](https://cloud.yandex.ru/docs/billing/quickstart/#create_billing_account)
2) [Установите CLI](https://cloud.yandex.ru/docs/cli/quickstart#install) и обязательно проверьте, что у вас работает команда
```
$ yc iam create-token
```
3. [Получите идентификатор](https://cloud.yandex.ru/docs/resource-manager/operations/folder/get-id) любого каталога, на который у вашего аккаунта есть роль editor или выше. Данный идентификатор необходимо сохранить в переменную folderId в файле main.py

Для использования телеграмм бота необходимо создать его с помощью @BotFather и полученный токен записать в переменную TOKEN в файле main.py
