requirements:
	pip install -r requirements.txt

migrate:
	python manage.py migrate

serve:
	python manage.py runserver

pep8:
	pep8 days

pylint:
	pylint days

quality: pep8 pylint
