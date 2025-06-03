# Pip needs to be < 25.1 for now because:
# https://github.com/jazzband/pip-tools/issues/2176
#
# Pinning for now until we migrate this whole thing over to the UV workflow
.PHONY: update-deps
update-deps:
	pip install --upgrade pip-tools "pip<25.1" setuptools
	pip-compile --upgrade --build-isolation --generate-hashes --output-file requirements/main.txt requirements/main.in
	pip-compile --upgrade --build-isolation --generate-hashes --output-file requirements/dev.txt requirements/dev.in

# Useful for testing against a Git version of Safir.
.PHONY: update-deps-no-hashes
update-deps-no-hashes:
	pip install --upgrade pip-tools "pip<25.1" setuptools
	pip-compile --upgrade --build-isolation --allow-unsafe --output-file requirements/main.txt requirements/main.in
	pip-compile --upgrade --build-isolation --allow-unsafe --output-file requirements/dev.txt requirements/dev.in

.PHONY: init
init:
	pip install --editable .
	pip install --upgrade -r requirements/main.txt -r requirements/dev.txt
	rm -rf .tox
	pip install --upgrade pre-commit "tox<4"
	pre-commit install

.PHONY: update
update: update-deps init

.PHONY: run
run:
	tox -e run
