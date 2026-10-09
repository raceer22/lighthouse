BLENDER ?= blender
DIST    := dist

.PHONY: test validate build install

test:
	.venv/bin/pytest -q

validate:
	$(BLENDER) --factory-startup --command extension validate lighthouse

build: validate
	mkdir -p $(DIST)
	$(BLENDER) --factory-startup --command extension build --source-dir lighthouse --output-dir $(DIST)

# Installs into the user_default repo and enables it in the user's Blender config.
install: build
	$(BLENDER) --factory-startup --command extension install-file -r user_default -e $(DIST)/lighthouse-*.zip
