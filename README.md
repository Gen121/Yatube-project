# Yatube-project - Социальная сеть блогеров

## Описание

Django веб-сайт на котором можно оставлять посты (включая изображения), оставлять коментарии, подписываться на любимых авторов.

## Технологии
Python 3.7, Django 2.2.19, pytest 6.2.4

## Как запустить проект в Dev режиме:

Клонировать репозиторий и перейти в него в командной строке:

```git
git clone https://github.com/Gen121/Yatube-project.git
```

```
cd Yatube-project
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

```
source venv/bin/activate          # for Linux
source venv/scripts/activate      # for Windows
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

В целях безопасности SECRET_KEY проекта размещен в окружении,
для работы с которым используется библиотека python-dotenv.
Для этого в проекте в директории /Yatube-project/yatube необходимо 
создать файл .env с ключом:

```
SECRET_KEY=you_shall_not_pass_for_example
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```
