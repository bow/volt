# Volt Makefile
# For development-related tasks automation


SHELL := /bin/bash

dev:
	pip install -r dev-requirements.txt

nose:
	nosetests volt/test/

cov:
	nosetests --cover-package=volt --with-coverage --cover-erase --cover-html --cover-html-dir=htmlcov
	cd htmlcov; python -m SimpleHTTPServer

cov-cli:
	nosetests --cover-package=volt --with-coverage --cover-erase

tox:
	rm -rf .tox/
	tox

clean:
	find . -name "*.pyc" -exec rm -f {} \;
	find . -name "*.class" -exec rm -f {} \;
	find . -name "__pycache__" -type d -exec rm -rf {} \;
