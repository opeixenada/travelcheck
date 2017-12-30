DOCKER = docker
NAME = travelcheck

GIT_VERSION := $(shell git describe --abbrev=7 --dirty --always --tags)

TAG = $(GIT_VERSION)

test:
	python -m unittest discover

build:
	$(DOCKER) build -t $(NAME) .

run:
	$(DOCKER) rm -f $(NAME) && $(DOCKER) run --name $(NAME) -d -p 8081:8081 $(NAME)

rm_containers:
	$(DOCKER) ps -aq | xargs $(DOCKER) rm || true

venv:
	eval $(source venv/bin/activate)
