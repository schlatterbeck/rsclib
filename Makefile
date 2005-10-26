LASTRELASE:=$(shell if x=`lastrelease -d` ;then echo $$x ;else echo 'NO_TAG' ;fi)
RSCLIB=__init__.py Config_File.py autosuper.py
VERSION=rsclib/Version.py
SRC=Makefile setup.py \
    $(RSCLIB:%.py=rsclib/%.py)

all: $(VERSION)

$(VERSION): $(SRC)

dist: all
	python setup.py sdist

%.py: %.v
	sed -e 's/RELEASE/$(LASTRELASE)/' $< > $@

clean:
	rm -f MANIFEST \
	    rsclib/Version.py
	rm -rf dist
