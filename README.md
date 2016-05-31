# days

Django application for learning about notable historical events.

### Local Development

Clone the code:

```
$ git clone git@github.com:rlucioni/days.git
```

Change into the cloned repository:

```
$ cd days
```

Create and activate a virtual environment.

```
$ python3 -m venv venv
$ source venv/bin/activate
```

Install requirements:

```
$ make requirements
```

Run migrations:

```
$ make migrate
```

Create a superuser:

```
$ python manage.py createsuperuser
```

Start the dev server at port 8000:

```
$ make serve
```

Access the app in your browser at `http://127.0.0.1:8000/`.


### Heroku

If you haven't already, install the [Heroku Toolbelt](https://devcenter.heroku.com/articles/getting-started-with-python#set-up). Create an app on Heroku:

```
$ heroku create
```

Export `DJANGO_SETTINGS_MODULE` and `DAYS_SECRET_KEY`:

```
$ heroku config:set DJANGO_SETTINGS_MODULE=days.settings.heroku
$ heroku config:set DAYS_SECRET_KEY=<secret>
```

Deploy the code:

```
$ git push heroku master
```

Ensure that at least one instance of the app is running:

```
$ heroku ps:scale web=1
```

Run migrations:

```
$ heroku run make migrate
```

Create a superuser:

```
$ heroku run python manage.py createsuperuser
```

Verify deployment by visiting the admin:

```
$ heroku open /admin
```
