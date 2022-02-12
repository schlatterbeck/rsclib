# To use this Makefile, get a copy of my SF Release Tools
# git clone git://git.code.sf.net/p/sfreleasetools/code sfreleasetools
# And point the environment variable RELEASETOOLS to the checkout
ifeq (,${RELEASETOOLS})
    RELEASETOOLS=../releasetools
endif
LASTRELEASE:=$(shell $(RELEASETOOLS)/lastrelease -n)
RSCLIB=ast_call.py ast_cdr.py ast_probe.py autosuper.py base_pickler.py \
    bero.py capacitance.py Config_File.py crm.py execute.py grepmime.py \
    hexdump.py inductance.py __init__.py IP_Address.py isdn.py          \
    iter_recipes.py lc_resonator.py Math.py nmap.py ocf.py              \
    PDF_Signature.py Phone.py PM_Value.py pycompat.py Rational.py       \
    sqlparser.py stateparser.py TeX_CSV_Writer.py timeout.py            \
    trafficshape.py
VERSIONPY=rsclib/Version.py
VERSION=$(VERSIONPY)
README=README.rst
SRC=Makefile setup.py $(RSCLIB:%.py=rsclib/%.py) \
    MANIFEST.in $(README) README.html

USERNAME=schlatterbeck
PROJECT=rsclib
PACKAGE=rsclib
CHANGES=changes
NOTES=notes

all: $(VERSION)

$(VERSION): $(SRC)

clean:
	rm -f MANIFEST rsclib/Version.py notes changes default.css    \
	      README.html README.aux README.dvi README.log README.out \
	      README.tex announce_pypi
	rm -rf dist build upload upload_homepage ReleaseNotes.txt

include $(RELEASETOOLS)/Makefile-pyrelease
