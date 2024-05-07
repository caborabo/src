jpeg:
	bash png_to_jpeg.sh

deps:
	pip install -r build/requirements.txt

generate:
	python -m build.generate

previews:
	python -m build.previews

transcribe:
	python -m build.transcribe

summarize:
	python -m build.summarize

chapters:
	python -m build.chapters

verify:
	CHECK_REMOTE=true python -m build.generate

clean:
	rm -rf ./docs/*.html
	rm -rf ./docs/assets/headshots/*.jpg
	rm -rf ./docs/assets/splash/*.jpg
	rm -rf ./docs/assets/podcasts/*.jpg

env:
	python3 -m venv env

all: deps jpeg generate transcribe summarize verify previews
.PHONY: deps jpeg generate transcribe summarize verify previews
