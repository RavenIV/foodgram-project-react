# FOODGRAM

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

Клонировать репозиторий:

```
git clone git@github.com:RavenIV/foodgram-project-react.git
```

Перейти в директорию infra/ и выполнить команду:
```
cd foodgram-project-react/infra/
docker compose up
```

Спецификация API будет доступна по адресу http://localhost/api/docs/


## Запустить бэкенд-приложение

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

В директории data/ доступны файлы в формате .json с ингредиентами и тегами.

Для загрузки ингредиентов и тегов в базу данных, находясь в директории backend/, выполните команды:

```
python manage.py load_ingredients ../data/ingredients.json
python manage.py load_tags ../data/tags.json
```


## Разработчики


* [Irina Vorontsova](https://github.com/RavenIV) - бэкенд