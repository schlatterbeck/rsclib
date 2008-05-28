LASTRELEASE:=$(shell ../svntools/lastrelease -n)
RSCLIB=__init__.py Config_File.py autosuper.py PM_Value.py IP4_Address.py \
    HTML_Parse.py PDF_Parse.py TeX_CSV_Writer.py
VERSION=rsclib/Version.py
SRC=Makefile setup.py $(RSCLIB:%.py=rsclib/%.py) \
    MANIFEST.in README README.html default.css

USERNAME=schlatterbeck
PROJECT=rsclib
PACKAGE=rsclib
CHANGES=changes
NOTES=notes
HOSTNAME=shell.sourceforge.net
PROJECTDIR=/home/groups/r/rs/rsclib/htdocs

all: $(VERSION)

$(VERSION): $(SRC)

dist: all
	python setup.py sdist --formats=gztar,zip

%.py: %.v
	sed -e 's/RELEASE/$(LASTRELEASE)/' $< > $@

README.html: README default.css
	rst2html --stylesheet=default.css $< > $@

default.css: ../../content/html/stylesheets/default.css
	cp ../../content/html/stylesheets/default.css .

upload_homepage: all
	scp README.html $(USERNAME)@$(HOSTNAME):$(PROJECTDIR)/index.html
	scp default.css $(USERNAME)@$(HOSTNAME):$(PROJECTDIR)

clean:
	rm -f MANIFEST rsclib/Version.py notes changes default.css README.html
	rm -rf dist build

include ../make/Makefile-sf
