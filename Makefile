requirements:
	pip install -r requirements.txt

migrate:
	python manage.py migrate

serve:
	python manage.py runserver
