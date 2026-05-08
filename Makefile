PYTHON ?= python3

.PHONY: all prepare-data real-data demo-data profile analyze clean

all: prepare-data analyze

prepare-data:
	@if [ -d /dataset ]; then \
		$(PYTHON) scripts/prepare_real_data.py; \
	elif [ -f data/raw/transcripts.csv ]; then \
		echo "Using provided data/raw/transcripts.csv"; \
	else \
		$(PYTHON) scripts/generate_synthetic_data.py; \
	fi

real-data:
	$(PYTHON) scripts/prepare_real_data.py

demo-data:
	$(PYTHON) scripts/generate_synthetic_data.py

profile: prepare-data
	$(PYTHON) scripts/profile_input.py

analyze:
	$(PYTHON) src/pipeline.py


clean:
	rm -f data/raw/transcripts.csv data/processed/*.csv data/processed/*.json figures/*.svg docs/executive_summary.md
