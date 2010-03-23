LASTRELEASE:=$(shell ../svntools/lastrelease -n)
RSCLIB=__init__.py Config_File.py autosuper.py PM_Value.py IP4_Address.py \
    HTML_Parse.py PDF_Parse.py TeX_CSV_Writer.py
VERSIONPY=rsclib/Version.py
VERSION=$(VERSIONPY)
SRC=Makefile setup.py $(RSCLIB:%.py=rsclib/%.py) \
    MANIFEST.in README README.html

USERNAME=schlatterbeck
PROJECT=rsclib
PACKAGE=rsclib
CHANGES=changes
NOTES=notes

all: $(VERSION)

$(VERSION): $(SRC)

dist: all
	python setup.py sdist --formats=gztar,zip

clean:
	rm -f MANIFEST rsclib/Version.py notes changes default.css \
	      README.html README.aux README.dvi README.log README.out \
	      README.tex
	rm -rf dist build upload upload_homepage

include ../make/Makefile-sf
