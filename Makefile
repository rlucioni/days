migrate:
	python manage.py migrate

pep8:
	pep8 days

pylint:
	pylint days

quality: pep8 pylint

requirements:
	pip install -r requirements/base.txt

serve:
	python manage.py runserver

.PHONY: migrate pep8 pylint quality requirements serve
