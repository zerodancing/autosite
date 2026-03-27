# Deploy on Render

Проект уже подготовлен под production-развёртывание:

- отдельный модуль `autoservice.settings_production`
- `WhiteNoise` для статики
- `gunicorn` как WSGI-сервер
- `collectstatic` и `check --deploy` в `build.sh`
- внешнее S3-совместимое хранилище для медиа через `django-storages`
- команда `sync_media_to_storage` для загрузки текущих локальных изображений

## Быстрый маршрут на 4 часа

1. Залить код в GitHub.
2. Создать PostgreSQL в Render.
3. Создать Web Service в Render из GitHub-репозитория.
4. Создать хранилище медиа, лучше всего Cloudflare R2.
5. Прописать переменные окружения.
6. Один раз выгрузить локальные картинки в внешний storage.
7. Проверить главную страницу, каталог, карточку авто, `/admin/`.
8. Подключить домен.

## 1. Как залить код в GitHub

Сначала создайте пустой репозиторий на GitHub без `README`, без `.gitignore`, без лицензии.

Дальше в папке `autosite/` выполните:

```bash
git init
git add .
git commit -m "Prepare project for production deployment"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

Если GitHub попросит авторизацию:

- через браузер подтвердите вход
- или используйте Personal Access Token вместо пароля

Важно:

- `.env` не должен попадать в GitHub
- папка `cars/` тоже не должна попадать в GitHub
- изображения будут жить во внешнем медиа-хранилище, а не в репозитории

## 2. Что создать в Render

Нужно два ресурса:

1. PostgreSQL
2. Web Service

Для Web Service можно использовать настройки из `render.yaml`.

Если хотите заполнить вручную:

- Build Command: `bash ./build.sh`
- Start Command: `gunicorn autoservice.wsgi:application --log-file -`

## 3. Переменные окружения

Минимальный production-набор:

```env
DJANGO_SETTINGS_MODULE=autoservice.settings_production
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=<long-random-secret-key>
DJANGO_SITE_URL=https://example.onrender.com
DJANGO_ALLOWED_HOSTS=example.onrender.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.onrender.com
DATABASE_URL=<render-postgres-url>
DJANGO_DB_CONN_MAX_AGE=600
DJANGO_SECURE_SSL_REDIRECT=1
DJANGO_SECURE_HSTS_SECONDS=3600
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=1
DJANGO_SECURE_HSTS_PRELOAD=0
AWS_STORAGE_BUCKET_NAME=autosite-media
AWS_S3_REGION_NAME=auto
AWS_S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
AWS_S3_CUSTOM_DOMAIN=<public-media-domain>
DJANGO_MEDIA_URL=https://<public-media-domain>/
AWS_ACCESS_KEY_ID=<access-key-id>
AWS_SECRET_ACCESS_KEY=<secret-access-key>
```

Примеры:

- `DJANGO_SITE_URL=https://my-autosite.onrender.com`
- `DJANGO_ALLOWED_HOSTS=my-autosite.onrender.com,www.example.com,example.com`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://my-autosite.onrender.com,https://www.example.com,https://example.com`
- `DJANGO_MEDIA_URL=https://media.example.com/`

Секретный ключ можно сгенерировать командой:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 4. Как настроить медиа, чтобы они не зависели от сервера

В production медиа должны храниться не на Render и не в GitHub, а во внешнем объектном хранилище.

Самый быстрый вариант:

- Cloudflare R2
- Backblaze B2 S3
- любой S3-совместимый storage

Для быстрого запуска подойдёт Cloudflare R2:

1. Создайте bucket, например `autosite-media`.
2. Включите публичную раздачу.
3. Получите:
   - `AWS_S3_ENDPOINT_URL`
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - публичный URL или отдельный поддомен для медиа
4. Пропишите `DJANGO_MEDIA_URL`.

После этого текущие локальные картинки нужно один раз отправить в bucket:

```bash
python manage.py sync_media_to_storage --settings autoservice.settings_production
```

Если нужно перезалить поверх:

```bash
python manage.py sync_media_to_storage --settings autoservice.settings_production --overwrite
```

Именно этот шаг делает изображения независимыми от сервера приложения.

## 5. Первый запуск после деплоя

Когда Render впервые соберёт сервис:

- `collectstatic` выполнится автоматически
- миграции применятся автоматически
- `check --deploy` выполнится автоматически

Потом в Shell сервиса выполните:

```bash
python manage.py createsuperuser
```

## 6. Как подключить домен

### Основной домен сайта

1. В Render откройте ваш Web Service.
2. Перейдите в `Settings -> Custom Domains`.
3. Добавьте домен, например `example.com` или `www.example.com`.
4. Render покажет DNS-запись, которую нужно создать у регистратора или DNS-провайдера.
5. После подтверждения домена обновите переменные:

```env
DJANGO_SITE_URL=https://example.com
DJANGO_ALLOWED_HOSTS=example.com,www.example.com,my-autosite.onrender.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com,https://my-autosite.onrender.com
```

### Отдельный домен для медиа

Лучший вариант:

- сайт отдаётся с `example.com`
- медиа отдаются с `media.example.com`

Тогда:

```env
AWS_S3_CUSTOM_DOMAIN=media.example.com
DJANGO_MEDIA_URL=https://media.example.com/
```

А сам `media.example.com` настраивается в DNS по инструкции вашего storage-провайдера.

## 7. Что проверить перед тем, как дать сайт друзьям

1. Главная открывается без 500 ошибки.
2. Каталог услуг открывается.
3. Каталог машин открывается.
4. Карточка машины показывает галерею.
5. `/admin/` открывается и даёт войти.
6. Новая загруженная картинка в админке открывается по адресу медиа-домена, а не по адресу Render-приложения.
7. Формы заказов и поддержки отправляются без CSRF-ошибок.
