BLENDER ?= blender
DIST    := dist
VERSION := $(shell sed -n 's/^version = "\(.*\)"/\1/p' lighthouse/blender_manifest.toml)

.PHONY: test bench validate build install

test:
	BLENDER=$(BLENDER) .venv/bin/pytest -q

# Times the Lights panel's draw with about 500 lights. Prints only, never fails on time.
bench:
	BLENDER=$(BLENDER) .venv/bin/python tests/bench_lights_panel.py

validate:
	$(BLENDER) --factory-startup --command extension validate lighthouse

build:
	BLENDER=$(BLENDER) ./build.sh $(DIST)

# Installs into the user_default repo and enables it in the user's Blender config.
install: build
	$(BLENDER) --factory-startup --command extension install-file -r user_default -e $(DIST)/lighthouse-$(VERSION).zip
