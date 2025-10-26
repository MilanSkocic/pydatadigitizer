ifeq ($(PLATFORM), windows)
	PY=py -
endif
ifeq ($(PLATFORM), linux)
	PY=python
	AW=auditwheel repair --plat manylinux_2_31_x86_64 ./dist/*.whl
endif
ifeq ($(PLATFORM), darwin)
	PY=python
endif

SETUP= setup.py pyproject.toml
PY_SRC=./src

.PHONY: doc docs clean

all: python3.14

python3.14: $(SETUP)
	@echo "########### PYTHON 3.14 ##########"
	$(PY)3.14 -m build --no-isolation --sdist
	$(PY)3.14 -m build --no-isolation --wheel
	@echo "#################################"

clean: 
	rm -rf build 
	rm -rf dist 
	rm -rf *.egg-info 
	rm -rf __pycache__ 
	rm -rf wheelhouse 
	rm -rf $(PY_SRC)/__pycache__
	rm -rf $(PY_SRC)/$(NAME).egg-info
	rm -f $(PY_SRC)/$(NAME)*.h 
	rm -f $(PY_SRC)/*.a 
	rm -f $(PY_SRC)/*.so 
	rm -f $(PY_SRC)/*.dylib 
	rm -f $(PY_SRC)/*.dll 
	rm -f $(PY_SRC)/*.dll.a 
	rm -f $(PY_SRC)/*.pyd
	rm -rf $(PY_SRC)/bin
	rm -rf $(PY_SRC)/include
	rm -rf $(PY_SRC)/lib
	make -C $(PY_SRC) clean

doc: 
	make -C doc latexpdf
	make -C doc html

docs:
	rm -rf ./docs/*
	cp -rf ./doc/build/html/* ./docs/
