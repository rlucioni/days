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

Start the dev server at port 8000:

```
$ make serve
```

Access the app in your browser at `http://127.0.0.1:8000/`.


### Heroku

Export `DJANGO_SETTINGS_MODULE` and `DAYS_SECRET_KEY`.
