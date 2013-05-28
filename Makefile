LASTRELEASE:=$(shell ../svntools/lastrelease -n)
RSCLIB=__init__.py Config_File.py autosuper.py PM_Value.py IP_Address.py \
    HTML_Parse.py PDF_Parse.py TeX_CSV_Writer.py base_pickler.py         \
    ast_call.py ast_cdr.py autosuper.py base_pickler.py bero.py          \
    capacitance.py Config_File.py ETree.py execute.py Firstname.py       \
    Freshmeat.py grepmime.py hexdump.py HTML_Parse.py inductance.py      \
    IP_Address.py iter_recipes.py isdn.py ldap_lib.py Math.py            \
    multipart_form.py nmap.py ocf.py PDF_Parse.py PDF_Signature.py       \
    Phone.py PM_Value.py Rational.py sqlparser.py stateparser.py         \
    TeX_CSV_Writer.py timeout.py trafficshape.py
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
	rm -f MANIFEST rsclib/Version.py notes changes default.css    \
	      README.html README.aux README.dvi README.log README.out \
	      README.tex announce_pypi
	rm -rf dist build upload upload_homepage ReleaseNotes.txt

include ../make/Makefile-sf
