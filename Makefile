LASTRELEASE:=$(shell ../svntools/lastrelease -n)
RSCLIB=__init__.py Config_File.py autosuper.py PM_Value.py IP4_Address.py \
    HTML_Parse.py PDF_Parse.py TeX_CSV_Writer.py
VERSION=rsclib/Version.py
SRC=Makefile setup.py \
    $(RSCLIB:%.py=rsclib/%.py)

all: $(VERSION)

$(VERSION): $(SRC)

dist: all
	python setup.py sdist --formats=gztar,zip

%.py: %.v
	sed -e 's/RELEASE/$(LASTRELEASE)/' $< > $@

clean:
	rm -f MANIFEST rsclib/Version.py
	rm -rf dist build
