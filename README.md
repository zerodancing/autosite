# Autosite

Учебный Django-проект для курсовой работы: сайт автосервиса и автокаталога с регистрацией пользователей, витриной машин и услуг, заявками на обслуживание/покупку и встроенным чатом поддержки.

README ниже задуман как одна точка входа в проект. По нему должно быть понятно:

- что делает сайт;
- что уже реализовано;
- как запустить проект локально;
- как выкатить изменения в прод;
- где хранятся данные, картинки и код;
- как управлять сайтом через GitHub, Render и Cloudinary;
- что делать, если сайт уснул, сломался деплой или пропали картинки;
- какие у проекта есть ограничения и риски.

## Быстрые ссылки

Актуально для текущего развёртывания проекта:

- Сайт: [https://autosite-zerodancing.onrender.com](https://autosite-zerodancing.onrender.com)
- Админка: [https://autosite-zerodancing.onrender.com/admin/](https://autosite-zerodancing.onrender.com/admin/)
- GitHub-репозиторий: [https://github.com/zerodancing/autosite](https://github.com/zerodancing/autosite)
- Render Dashboard: [https://dashboard.render.com/](https://dashboard.render.com/)
- Cloudinary Console: [https://console.cloudinary.com/](https://console.cloudinary.com/)
- Cloudinary Media Library: [https://console.cloudinary.com/](https://console.cloudinary.com/)

## Что это за проект

Сайт совмещает несколько сценариев в одном интерфейсе:

1. Витрина автомобилей.
2. Каталог услуг автосервиса.
3. Личный кабинет пользователя.
4. Оформление заявок:
   - запись на услугу;
   - заявка по автомобилю.
5. Встроенная поддержка с перепиской клиент <-> оператор.
6. Админка для управления всем этим через Django Admin.

По сути это не просто лендинг, а полноценное CRUD-веб-приложение для демонстрации курсового проекта.

## Что уже реализовано

### Пользовательская часть

- Главная страница с современной витриной, быстрым поиском и подборками.
- Каталог машин:
  - список;
  - фильтрация по категории;
  - поиск по марке, модели и описанию;
  - карточка автомобиля;
  - галерея изображений;
  - характеристики автомобиля.
- Каталог услуг:
  - список;
  - фильтрация по категории;
  - поиск;
  - карточка услуги.
- Регистрация пользователя.
- Вход по `username` или `email`.
- Профиль пользователя.
- Переключение языка интерфейса.
- Переключение темы интерфейса.
- Оформление заявок:
  - на услугу с желаемым временем;
  - на автомобиль.
- Страница "Мои заказы".
- Страница отдельного заказа.
- Раздел поддержки:
  - создание нового обращения;
  - просмотр истории диалогов;
  - переписка в чате;
  - отправка изображений;
  - отправка голосовых сообщений;
  - запись голосового сообщения прямо в браузере;
  - polling/AJAX-обновление сообщений с мягким backoff при ошибках.

### Административная часть

- Django Admin на русском языке.
- Управление пользователями и ролями.
- Управление категориями услуг и самими услугами.
- Управление категориями машин и машинами.
- Загрузка и управление галереей изображений машин.
- Управление характеристиками машин и их значениями.
- Просмотр и обработка заказов.
- Просмотр диалогов поддержки и сообщений.
- Просмотр фото и прослушивание голосовых сообщений в админке.

### Что подтверждено кодом и тестами

В проекте уже есть автотесты на:

- logout через `POST`;
- вход по email;
- безопасное переключение языка;
- временную блокировку брутфорса на логине;
- загрузку галереи автомобилей;
- генерацию URL изображений;
- создание заказов;
- валидацию даты записи на услугу;
- валидацию комментариев;
- права доступа к чатам;
- отправку голосовых сообщений;
- создание обращения только с изображением без текста;
- мягкий rate limit на отправку сообщений в поддержку;
- CSRF для отправки сообщений;
- назначение оператора в чате.

На момент обновления этого README локально проходит `23` теста:

```bash
python manage.py test
```

Также в репозитории добавлен GitHub Actions workflow, который запускает `manage.py check` и `manage.py test` на push и pull request.

## Текущая архитектура

### Прод

Текущий production устроен так:

- исходный код хранится на GitHub;
- приложение развёрнуто на Render как Python Web Service;
- регион текущего сервиса: Frankfurt;
- Django запускается через `gunicorn`;
- `DEBUG=False`;
- статика собирается через `collectstatic`;
- статика раздаётся через WhiteNoise;
- база данных хранится в Render Postgres;
- пользовательские изображения и медиа хранятся во внешнем storage, сейчас проект рассчитан на Cloudinary или S3-совместимое хранилище;
- Cloudinary storage в проекте настроен не только на изображения, но и на голосовые вложения;
- для текущего развёртывания медиа вынесены в Cloudinary;
- файловая система Render считается временной, поэтому хранить продовые медиа внутри контейнера нельзя.

### Локально

Локально проект может работать проще:

- база: `db.sqlite3`;
- картинки: локальная папка `cars/`;
- запуск: `python manage.py runserver` или через `start.ps1` / `start.cmd`.
- часовой пояс проекта по умолчанию: `Europe/Moscow` с возможностью переопределить через `DJANGO_TIME_ZONE`.

Если работа идёт на исходном компьютере автора проекта, исходная папка с фотографиями была такой:

```text
C:\Users\zerno\Desktop\Общая папка ВМ\Курсовая сайт Автосервис\autosite\cars
```

Если проект открыт в другой директории, ориентируйся уже на локальную папку `cars/` внутри текущего checkout.

## Основные сущности

Ключевые модели проекта:

- `accounts.CustomUser`:
  - пользователь;
  - роль;
  - ФИО;
  - телефон.
- `catalog.ServiceCategory` и `catalog.Service`:
  - категории услуг;
  - услуги.
- `catalog.CarCategory` и `catalog.Car`:
  - категории машин;
  - карточки машин.
- `catalog.CarImage`:
  - галерея изображений машины.
- `catalog.CarCharacteristicGroup`, `CarCharacteristic`, `CarCharacteristicValue`:
  - характеристики автомобиля.
- `orders.Order`:
  - заявки на услугу или автомобиль.
- `support.Conversation` и `support.Message`:
  - поддержка и переписка.

Подробная схема есть в [docs/ERD.md](docs/ERD.md).

## Стек

- Backend: Django 6
- WSGI: Gunicorn
- БД:
  - локально `SQLite`;
  - в проде `PostgreSQL`
- Шаблоны: Django Templates
- UI: Tailwind CSS через CDN
- Медиа:
  - локально `cars/`;
  - в проде `Cloudinary` или S3-compatible storage
- Статика в проде: WhiteNoise
- Внешний хостинг: Render

## Структура проекта

```text
autosite/
├─ accounts/                 # аккаунты, авторизация, профиль, роли, bootstrap superuser
├─ autoservice/              # settings, urls, middleware, storage backends
├─ catalog/                  # услуги, машины, характеристики, загрузка медиа, demo fixture
├─ orders/                   # заказы и формы заявок
├─ support/                  # чат поддержки и API polling
├─ templates/                # HTML-шаблоны
├─ docs/                     # дополнительная документация
├─ scripts/                  # вспомогательные скрипты
├─ cars/                     # локальные исходные изображения, не для git/prod
├─ build.sh                  # build-скрипт для Render
├─ render.yaml               # инфраструктурный конфиг Render
├─ requirements.txt          # Python-зависимости
├─ start.ps1                 # быстрый запуск на Windows PowerShell
├─ start.cmd                 # быстрый запуск на Windows CMD
└─ manage.py
```

## Как запустить локально

### Вариант 1. Самый быстрый для Windows

PowerShell:

```powershell
.\start.ps1
```

или CMD:

```cmd
start.cmd
```

Что делают эти скрипты:

1. Переходят в папку проекта.
2. Находят `venv` или `.venv`.
3. При первом запуске ставят зависимости.
4. Применяют миграции.
5. Открывают браузер.
6. Запускают `runserver` на `127.0.0.1:8000`.

### Вариант 2. Ручной запуск

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

После запуска:

- Главная: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Админка: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- Поддержка: [http://127.0.0.1:8000/support/](http://127.0.0.1:8000/support/)

### Локальный администратор

Классический способ:

```bash
python manage.py createsuperuser
```

Dev-хелпер для режима `DEBUG=True`:

```text
/accounts/dev-admin-setup/
```

Этот endpoint создаёт/обновляет локального админа только в dev-режиме. В проде он отключён.

## Как входить в систему

- Пользователь может войти по логину или по email.
- Logout работает только через `POST`, что безопаснее обычной `GET`-ссылки.
- В админке интерфейс принудительно держится на русском языке.

## Как управлять контентом через админку

Через `/admin/` можно:

- создавать и редактировать пользователей;
- назначать роли;
- создавать категории услуг и сами услуги;
- создавать категории машин и карточки машин;
- загружать изображения машин;
- задавать характеристики автомобилей;
- смотреть и менять статусы заказов;
- читать обращения поддержки и отвечать в чатах.

### Как добавлять машины

1. Открой `/admin/`.
2. Создай или выбери `CarCategory`.
3. Создай `Car`.
4. Добавь изображения галереи.
5. При необходимости добавь характеристики.
6. Убедись, что `is_active=True`.

### Как добавлять услуги

1. Открой `/admin/`.
2. Создай или выбери `ServiceCategory`.
3. Создай `Service`.
4. Задай цену, длительность, описание.
5. Добавь изображение.
6. Убедись, что `is_active=True`.

## Где что хранится

### В проде

- Код: GitHub
- Веб-приложение: Render
- База данных: Render Postgres
- Изображения и медиа: Cloudinary
- Статика: внутри deploy-артефакта Render после `collectstatic`

### Локально

- Код: локальная папка проекта
- Локальная база: `db.sqlite3`
- Локальные исходные изображения: `cars/`

## Как устроен деплой

### Основной сценарий

Обычный цикл работы такой:

```bash
git add .
git commit -m "Описание изменений"
git push origin main
```

После пуша в `main` Render делает новый деплой автоматически, если `Auto-Deploy` включён.

### Что делает Render при сборке

См. [build.sh](build.sh):

1. ставит зависимости;
2. запускает `collectstatic --clear`;
3. применяет миграции;
4. выполняет `ensure_bootstrap_superuser`;
5. выполняет `ensure_demo_catalog`;
6. выполняет `check --deploy`.

### Конфиг Render

См. [render.yaml](render.yaml). Там зафиксированы:

- `DJANGO_SETTINGS_MODULE=autoservice.settings_production`
- `DJANGO_DEBUG=0`
- build command: `bash ./build.sh`
- start command: `gunicorn autoservice.wsgi:application --log-file -`

## Как управлять сайтом на Render

### Если сайт "выключился"

На free-плане Render сервис обычно не нужно вручную включать. Если он уснул, просто открой сайт по URL, и он проснётся сам.

### Если нужно перезапустить текущую версию

Render -> Web Service -> `Manual Deploy` -> `Restart service`

### Если нужно выкатить последний код с GitHub

Либо:

```bash
git push origin main
```

либо в Render:

`Manual Deploy` -> `Deploy latest commit`

### Если не нужен автодеплой на каждый push

Render -> сервис -> `Settings` -> отключить `Auto-Deploy`

### Если подозрение на битый кэш сборки

Render -> `Manual Deploy` -> `Clear build cache & deploy`

### Если нужен разбор ошибки

Render -> сервис -> `Logs`

### Если нужно проверить переменные окружения

Render -> сервис -> `Environment`

### Если нужно поменять режимы сборки и запуска

Render -> сервис -> `Settings`

## Free-план Render: что важно помнить

Для текущей инфраструктуры это очень важно:

- web service засыпает примерно через `15 минут` без трафика;
- при следующем открытии сам просыпается;
- пробуждение может занимать до минуты;
- у free web service нет persistent disk;
- у free web service нет shell;
- у free web service нет one-off jobs;
- на workspace даётся `750 instance hours` в месяц;
- если часы кончатся, free web services будут приостановлены до следующего месяца.

### Важно по базе данных

Free Render Postgres живёт ограниченное время.

Для текущей базы, если она была создана `27 марта 2026`, ориентиры такие:

- окончание срока free-базы: примерно `26 апреля 2026`;
- льготный период перед удалением: ещё около `14 дней`;
- возможное удаление без апгрейда: примерно после `10 мая 2026`.

Если сайт нужен дольше тестов, базу надо перевести на платный тариф или перенести на другой сервер.

## Почему медиа нельзя хранить прямо на Render

Потому что файловая система контейнера временная. Всё, что будет сохраняться внутрь самого сервиса, может потеряться после деплоя или рестарта.

Поэтому в проекте сделано правильное разделение:

- база отдельно;
- код отдельно;
- медиа отдельно.

## Cloudinary и медиа

### Как это работает сейчас

- Локально картинки могут жить в `cars/`.
- В production медиа должны жить во внешнем хранилище.
- Проект умеет работать:
  - с Cloudinary;
  - с S3-compatible storage.
- Для чата поддержки во внешнее хранилище также уходят:
  - изображения;
  - голосовые сообщения.

### Что используется сейчас

Для текущего развёртывания основной и самый удобный вариант - Cloudinary.

Нужные переменные:

- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

### Где смотреть картинки

Cloudinary Console -> Assets / Media Library

### Что делать, если через админку загрузили фото, а они не открываются

Проверить:

1. что в Render заданы Cloudinary-переменные;
2. что в Cloudinary картинка реально появилась;
3. что `MEDIA_URL` и storage backend корректно поднялись в проде;
4. что в логах нет `ImproperlyConfigured`.

## Как перелить локальные картинки во внешнее хранилище

Если есть локальная папка `cars/`, а проект уже настроен на production storage:

```bash
python manage.py sync_media_to_storage --settings autoservice.settings_production
```

Если нужно перезалить поверх:

```bash
python manage.py sync_media_to_storage --settings autoservice.settings_production --overwrite
```

Важно: команда специально проверяет, что `default_storage` не указывает на локальный `MEDIA_ROOT`.

## Демо-данные каталога

В проекте есть fixture:

```text
catalog/fixtures/catalog_demo_seed.json
```

Он содержит демо-каталог машин и может автоматически загрузиться в пустую базу.

### Управление через env

```env
DJANGO_LOAD_DEMO_FIXTURE=0
```

Если поставить `1`, build-скрипт сможет подгрузить демо-каталог в пустую базу.

### Ручной запуск

```bash
python manage.py ensure_demo_catalog --force
```

### Практическая рекомендация

Если ты уже убедился, что каталог машин загружен и всё на месте, лучше держать:

```env
DJANGO_LOAD_DEMO_FIXTURE=0
```

Если в текущем Render-окружении это временно стоит в `1`, после проверки лучше вернуть обратно в `0`.

## Автосоздание суперпользователя при деплое

В проекте есть команда:

```bash
python manage.py ensure_bootstrap_superuser
```

Она срабатывает только если явно включить:

```env
DJANGO_BOOTSTRAP_SUPERUSER=1
DJANGO_BOOTSTRAP_SUPERUSER_USERNAME=...
DJANGO_BOOTSTRAP_SUPERUSER_PASSWORD=...
DJANGO_BOOTSTRAP_SUPERUSER_EMAIL=...
```

Если эта связка не нужна, оставляй:

```env
DJANGO_BOOTSTRAP_SUPERUSER=0
```

## Переменные окружения

Актуальный шаблон см. в [.env.production.example](.env.production.example).

Минимально важные production-переменные:

```env
DJANGO_SETTINGS_MODULE=autoservice.settings_production
DJANGO_DEBUG=0
DJANGO_TIME_ZONE=Europe/Moscow
DJANGO_SECRET_KEY=replace-with-a-long-random-secret-key
DJANGO_SITE_URL=https://example.com
DJANGO_ALLOWED_HOSTS=example.com,www.example.com,example.onrender.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com,https://example.onrender.com
DATABASE_URL=postgresql://user:password@host:5432/database
DJANGO_DB_CONN_MAX_AGE=600
DJANGO_BOOTSTRAP_SUPERUSER=0
DJANGO_LOAD_DEMO_FIXTURE=0
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

### Важные замечания

- В production обязателен `DJANGO_SECRET_KEY`.
- В production обязателен корректный `DATABASE_URL` или Postgres-настройки.
- Для production обязателен внешний storage для медиа.
- Если Cloudinary не настроен, должен быть настроен S3-compatible storage.
- Без корректных `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS` проект не должен стартовать.

## Команды, которые полезно помнить

### Базовые

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
python manage.py check
python manage.py test
```

### Production-проверки

```bash
python manage.py check --deploy
```

### Работа с демо-данными

```bash
python manage.py ensure_demo_catalog --force
```

### Работа с медиа

```bash
python manage.py sync_media_to_storage --settings autoservice.settings_production
```

## Что делать в типовых ситуациях

### Сайт долго открывается

Скорее всего, Render-экземпляр уснул. Для free-плана это нормально.

### После пуша сайт не обновился

Проверь:

1. пуш точно ушёл в `main`;
2. в Render включён `Auto-Deploy`;
3. деплой не упал в логах;
4. при необходимости запусти `Deploy latest commit`.

### После деплоя что-то сломалось

Порядок проверки:

1. Logs в Render;
2. env-переменные;
3. `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS`;
4. `DATABASE_URL`;
5. Cloudinary credentials;
6. при странном кэше `Clear build cache & deploy`.

### Пользовательские картинки пропадают

Проверь, не сохранились ли они в локальную файловую систему вместо Cloudinary. В production так делать нельзя.

### Локально не ставятся зависимости через `start.ps1` / `start.cmd`

Скрипты используют файл `.deps_ready` как маркер, что зависимости уже ставились. Если ты менял `requirements.txt`, проще вручную выполнить:

```bash
pip install -r requirements.txt
```

или удалить `.deps_ready` и запустить скрипт снова.

## Безопасность

Кратко:

- CSRF включён;
- XSS снижается за счёт autoescape и безопасной вставки текста;
- закрытые страницы защищены через `login_required`;
- logout переведён на `POST`;
- есть базовые security headers;
- есть лёгкий cache-based rate limit на логин, создание обращений, отправку сообщений и polling чата;
- есть мягкая временная блокировка брутфорса на логине;
- в чате есть простейший антиспам-лимит на частую отправку подряд;
- загрузки в чат ограничены по типу и размеру файлов;
- редирект при переключении языка проверяется безопасно.

Подробнее см. [docs/SECURITY.md](docs/SECURITY.md).

## Что стоит поменять после тестов

Если проект будет жить дольше демонстрации или пойдёт в публичный доступ, стоит обязательно:

1. Поставить `DJANGO_LOAD_DEMO_FIXTURE=0`.
2. Поменять `CLOUDINARY_API_SECRET`.
3. Поменять `DATABASE_URL` или пароль базы.
4. Поменять `DJANGO_SECRET_KEY`.
5. Проверить `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS`.
6. Подумать о переезде с free Postgres.

## Ограничения и слабые места проекта

Это хороший учебный проект, но важно честно понимать его границы:

1. Нет реальных платежей и платёжных интеграций.
2. Чат построен на polling, а не на WebSocket-реальном времени.
3. Free Render засыпает и ограничен по ресурсам.
4. Free Postgres на Render временный и может быть удалён по сроку.
5. Тесты уже есть и теперь гоняются в CI, но покрытие всё ещё частичное.
6. Лёгкие rate limits реализованы на локальном кэше Django, а не на внешнем edge/WAF, поэтому это базовая защита, а не полноценная анти-DDoS-инфраструктура.
7. Прод целиком зависит от корректных внешних env-переменных и внешних сервисов.
8. Медиа в проде нельзя хранить в контейнере Render, только во внешнем storage.

## Что я бы улучшал дальше

Если будет время развивать проект после курсовой, хороший порядок такой:

1. Расширить тесты на каталог, авторизацию и админские сценарии.
2. Добавить нормальные роли и разграничение прав операторов.
3. Перевести чат на WebSocket/Channels.
4. Сделать резервное копирование базы и медиа.
5. Убрать зависимость от free Postgres.

## Полезные файлы в репозитории

- [render.yaml](render.yaml) - конфиг развёртывания Render
- [build.sh](build.sh) - build/deploy pipeline
- [.env.production.example](.env.production.example) - пример production-env
- [.github/workflows/django-tests.yml](.github/workflows/django-tests.yml) - CI-проверка `check` и `test`
- [docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md) - заметки по деплою
- [docs/SECURITY.md](docs/SECURITY.md) - безопасность
- [docs/ERD.md](docs/ERD.md) - схема данных

## Внешняя документация

- Render free plan: [https://render.com/docs/free](https://render.com/docs/free)
- Render deploys: [https://render.com/docs/deploys](https://render.com/docs/deploys)
- Render + Django: [https://render.com/docs/deploy-django](https://render.com/docs/deploy-django)
- Cloudinary Django integration: [https://cloudinary.com/documentation/django_integration](https://cloudinary.com/documentation/django_integration)

## Короткий рабочий регламент

Если нужен совсем короткий сценарий на каждый день:

1. Меняешь код локально.
2. Проверяешь сайт локально.
3. Запускаешь `python manage.py test`.
4. Делаешь `git add`, `git commit`, `git push`.
5. Проверяешь деплой в Render.
6. Если нужно, смотришь логи.
7. Если сайт уснул, просто открываешь URL.
8. Если сломался кэш сборки, делаешь `Clear build cache & deploy`.
9. Контент редактируешь через `/admin/`.
10. Картинки смотришь в Cloudinary Media Library.

---

Если README перестаёт совпадать с реальностью, обновляй в первую очередь:

- ссылки;
- env-переменные;
- способ хранения медиа;
- build/start-команды;
- ограничения хостинга;
- порядок деплоя.
