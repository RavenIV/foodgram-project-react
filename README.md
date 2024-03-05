# FOODGRAM

[![Main Foodgram workflow](https://github.com/RavenIV/foodgram-project-react/actions/workflows/main.yml/badge.svg)](https://github.com/RavenIV/foodgram-project-react/actions/workflows/main.yml)

**Foodgram** - сайт, на котором пользователи могут публиковать рецепты, 
добавлять чужие рецепты в избранное и подписываться на публикации других авторов. 
Пользователям также доступно создание списка продуктов, которые необходимо купить 
для приготовления выбранных блюд.


## Стек технологий

* Python (3.9)
* Django (3.2.3)
* Django REST framework (3.12.4)
* Djoser (2.1.0)
* Docker
* Gunicorn


## Запустить проект 

Установить [Docker](https://www.docker.com/).

Клонировать репозиторий и перейти в него в командной строке:

```
cd foodgram-project-react/
git clone git@github.com:RavenIV/foodgram-project-react.git
```

Скопировать содержание .env.example в .env

Собрать контейнеры и выполнить команду:

```
docker compose up -d
```

Выполнить миграции:
```
docker compose exec backend python manage.py migrate
```

Собрать и перенести статику бэкенда:

```
docker compose exec backend python manage.py collectstatic
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/
```

Спецификация API будет доступна по адресу http://localhost/api/docs/


## Демо

[**foodgram**](https://foodgram-iv.sytes.net/)


## Переменные окружения


В файл .env также можно добавить:

* IP-адрес, доменное имя

```
ALLOWED_HOSTS=127.0.0.1,localhost,<your_host>,<domain_name>
```

* порт PostgreSQL в контейнере (по умолчанию 5432)

```
DB_PORT=0000
``` 

* включение режима разработки

```
DEBUG=True
``` 

* использование SQLite

```
USE_SQLITE=True
```

## Запустить бэкенд-приложение локально

Перейти в директорию бэкенд-приложения в командной строке:

```
cd backend
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

* Если у вас Linux/macOS

    ```
    source env/bin/activate
    ```

* Если у вас windows

    ```
    source env/scripts/activate
    ```

```
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить приложение:

```
python3 manage.py runserver
```

## Иморт данных

В директории backend/data/ доступны файлы в формате .json с ингредиентами и тегами.

Для загрузки ингредиентов и тегов в базу данных, находясь в директории backend/, выполните команды:

```
python manage.py load_ingredients data/ingredients.json
python manage.py load_tags data/tags.json
```


## Разработчики


* [Irina Vorontsova](https://github.com/RavenIV) - бэкенд