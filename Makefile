BLENDER ?= blender
DIST    := dist
VERSION := $(shell sed -n 's/^version = "\(.*\)"/\1/p' lighthouse/blender_manifest.toml)

.PHONY: test validate build install

test:
	BLENDER=$(BLENDER) .venv/bin/pytest -q

validate:
	$(BLENDER) --factory-startup --command extension validate lighthouse

build:
	BLENDER=$(BLENDER) ./build.sh $(DIST)

# Installs into the user_default repo and enables it in the user's Blender config.
install: build
	$(BLENDER) --factory-startup --command extension install-file -r user_default -e $(DIST)/lighthouse-$(VERSION).zip
