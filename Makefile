# Volt Makefile
# For development-related tasks automation


SHELL := /bin/bash

dev:
	pip install -r dev-requirements.txt

nose:
	nosetests volt/test/

2to3:
	if test -d .volt; \
	then echo "None detected."; \
	else cp -r volt .volt; \
	2to3 -W -n volt; \
	fi

3to2:
	if test -d .volt; \
	then rm -rf volt/; mv .volt volt; \
	fi

cov:
	#nosetests --cover-package=volt --with-coverage --cover-erase --cover-html --cover-html-dir=htmlcov
	cd volt; coverage run `which nosetests`
	cd volt; coverage html --omit=*test* --ignore-errors
	cd volt/htmlcov; python -m SimpleHTTPServer

cov-cli:
	nosetests --cover-package=volt --with-coverage --cover-erase

tox:
	rm -rf .tox/
	tox

clean:
	find . -name "*.pyc" -exec rm -f {} \;
	find . -name "*.class" -exec rm -f {} \;
	find . -name "*.coverage" -exec rm -f {} \;
	find . -name "*__pycache__" -type d -exec rm -rf {} \;
	find . -name "*htmlcov" -type d -exec rm -rf {} \;
