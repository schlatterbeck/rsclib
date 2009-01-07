#!/usr/bin/python
# Copyright (C) 2005-07 Dr. Ralf Schlatterbeck Open Source Consulting.
# Reichergasse 131, A-3411 Weidling.
# Web: http://www.runtux.com Email: office@runtux.com
# All rights reserved
# ****************************************************************************
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Library General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
# ****************************************************************************

from base64                import b64decode
from itertools             import islice
from pyPdf                 import PdfFileReader
from pyasn1.codec.der      import decoder as der
from pyasn1.codec.ber      import decoder as ber
from xml.etree.ElementTree import fromstring

class PDF_Signature :
    """
        Get signature from a PDF file
        This uses the standard Acrobat-defined way as defined in the pdf
        spec. For now we only support /Filter Adobe.PkLite and
        /SubFilter adbe.x509.rsa_sha1
    """
    def __init__ (self, pdf_file) :
        if not hasattr (pdf_file, "read") :
            pdf_file = open (pdf_file, "rb")
        self.reader  = PdfFileReader (pdf_file)
        self.catalog = c = self.reader.trailer ['/Root']
        print "Catalog:", c
        print c ['/AcroForm']['/Fields'][0].getObject()['/V']
    # end def __init__
# end class PDF_Signature

class PDF_Trodat_Signature :
    """
        Get the signature from a PDF file
        Interesting components:
        - TSTInfo_Xml: An XML snippet inside the Seal XML containing a
          "HashedMessage" part which is base64 encoded
        - LtcCertificate: ASN.1 DER encoded Certificate
        - TSTInfo_Signature: A ASN.1 DER encoded signature
        - LtcSignature: base64 encoded binary data
        - DocumentHash: base64 encoded binary data
    """

    def __init__ (self, pdf_file) :
        if not hasattr (pdf_file, "read") :
            pdf_file = open (pdf_file, "rb")
        self.reader  = PdfFileReader (pdf_file)
        self.catalog = c = self.reader.trailer ['/Root']
        print "Catalog:", c
        self.seal    = c ['/TRO_TrodatSeal'].getObject () [0].getObject ()
        assert (self.seal ['/Type'] == '/TRO_TrodatSealSignature')
        print "Seal:", self.seal
        pages        = c ['/Pages']
        print "Kids:", pages ['/Kids']
        content      = []
        for k in pages ['/Kids'] :
            print "kid:", k.getObject ()
            print "pdf:", k.pdf
            content.append (k.getObject ())
        print content
        print "Pages:", pages
        labels       = c ['/PageLabels']
        print "Labels:", labels
        self.barcode = self.seal ['/BarCode'].getData ()
        xml          = self.seal ['/SecInfo'].getData ()
        self.xml     = ''.join (x for x in islice (xml, 0, None, 2))
        self.tree    = fromstring (self.xml)
        print "SecInfo:", self.seal ['/SecInfo']
        print "\nXML:"
        print self.xml
        signator     = self.tree [0]
        assert (signator.tag == "signator")
        for node in signator :
            print "%s: %s" % (node.tag, node.text),
            for k, v in node.attrib.iteritems () :
                print "%s = %s " % (k, v),
            print
        for c in "TSTInfo_Xml DocumentHash LtcSignature".split () :
            print c
            cert = b64decode (self.tree.find ('.//%s' % c).text)
            print cert
            for b in cert :
                print "%02X " % ord (b),
            print
            if c == "TSTInfo_Xml" :
                tsttree = fromstring ("<xml>" + cert + "</xml>")
                hm = b64decode (tsttree.find ('.//HashedMessage').text)
                print "HashedMessage:"
                print hm
                for b in hm :
                    print "%02X " % ord (b),
                print
        for c in "LtcCertificate TSTInfo_Signature".split () :
            print c
            cert = self.tree.find ('.//%s' % c).text
            print der.decode (b64decode (cert))
    # end def __init__

# end class PDF_Trodat_Signature

if __name__ == "__main__" :
    #sig = PDF_Trodat_Signature \
    #    ("/home/ralf/200809171_HN_online_Schlatterbeck.pdf")
    sig = PDF_Signature ("/home/ralf/451719664-00.pdf")
