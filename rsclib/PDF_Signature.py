#!/usr/bin/python
# Copyright (C) 2008-17 Dr. Ralf Schlatterbeck Open Source Consulting.
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

from __future__            import print_function
import os
from hashlib               import sha1
from base64                import b64decode, encodestring
from itertools             import islice
from PyPDF2                import PdfFileReader
from pyasn1.codec.der      import decoder as der
from pyasn1.codec.ber      import decoder as ber
from xml.etree.ElementTree import fromstring
from rsclib.iter_recipes   import grouper
from _TFL                  import TFL, Numeric_Interval, Interval_Set
# Not yet available for python3:
from M2Crypto              import RSA, X509, m2, m2urllib2, BIO, Err

try :
    from io                import StringIO
except ImportError :
    from cStringIO         import StringIO

class Signature_Error   (ValueError)          : pass
class Signature_Unknown (NotImplementedError) : pass

class PDF_Signature :
    """
        Get signature from a PDF file
        This uses the standard Acrobat-defined way as defined in the pdf
        spec. For now we only support /Filter Adobe.PkLite and
        /SubFilter adbe.x509.rsa_sha1.
        We also don't support partially signed documents (where the
        signed range doesn't include the whole document) or multiple
        signatures on a document.
        For now we also do not support revocation-list checking.
        Oh, and we only support a single certificate, although PDF
        supports to give a whole cert chain (in a PDF array)
        We *do* check the purpose of the certificate and try to chain
        up to a trusted cert for which you can specify the location.

        We expect the trusted certificate file to be in PEM format and
        have the name (or symlink) of its hash computed with
        openssl x509 -noout -in cert.pem -hash
        and a trailing .<number>, a good intro is in
        http://www.madboa.com/geek/openssl/#verify-new
        Openssl comes with a program to create these symlinks called
        c_rehash.

        To convert from pcs7 format (extension is sometimes .p7b) use
        the pkcs7 subcommand from openssl, e.g.,
        openssl pkcs7 -in x.p7b -inform DER -print_certs

        FIXME: SSL-specific stuff (certificate chain verification etc.)
        should probably be moved to its own module.
    """
    supported = \
        { 'Filter'    : { '/Adobe.PPKLite'      : 1 }
        , 'SubFilter' : { '/adbe.x509.rsa_sha1' : 1 }
        }
    def __init__ (self, pdf_file, cert_location = '/etc/ssl/certs') :
        self.cert_location = cert_location
        self._status       = []
        if not hasattr (pdf_file, "read") :
            pdf_file       = open (pdf_file, "rb")
        self.contents      = pdf_file.read ()
        f                  = StringIO (self.contents)
        self.reader        = PdfFileReader (f)
        self.catalog       = c = self.reader.trailer ['/Root']
        try :
            sig = c ['/AcroForm']['/Fields'][0].getObject()['/V']
        except KeyError :
            raise Signature_Error ("PDF File doesn't seem to have a signature")
        if '/ByteRange' not in sig :
            raise Signature_Unknown ("Not a byte range signature")
        for k, v in self.supported.iteritems () :
            if '/%s' % k not in sig :
                raise Signature_Unknown ("Signature doesn't define %s" % k)
            stype = sig ['/%s' % k]
            if stype not in v :
                raise Signature_Unknown ("Unknown %s: %s" % (k, stype))
        IS   = TFL.Interval_Set
        NI   = TFL.Numeric_Interval
        iv   = IS (NI (0, len (self.contents) - 1))
        hash = sha1 ()
        for start, length in grouper (2, sig ['/ByteRange']) :
            iv = iv.difference (IS (NI (start, start + length - 1)))
            hash.update (self.contents [start : start + length])
        self.digest = hash.digest ()
        l = len (iv.intervals)
        if l != 1 :
            raise Signature_Error ("Number of non-signed Intervals %s != 1" % l)
        iv = iv.intervals [0]
        sig_contents = self.contents [iv.lower : iv.upper].strip ()
        assert (sig_contents  [0] == '<')
        assert (sig_contents [-1] == '>')
        sig_contents = sig_contents [1:-1].decode ('hex')
        self.sig     = sig ['/Contents']
        if self.sig != sig_contents :
            raise Signature_Error ("Invalid byte-range for signature")
        self._status.append \
            ("Byte range defined over whole document except signature, OK")
        self.sig = str (der.decode (self.sig) [0])
        #print (ber.decode (self.sig)) # works too (der is a subset of ber)
        # Seems the Cert is DER encoded. Beware of a just-reported bug
        # in pyPdf:
        # http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=511252
        # also present in 1.12 of upstream.
        # openssl asn1parse -inform DER -in z
        self.cert   = X509.load_cert_der_string (sig ['/Cert'])
        for purpose in m2.X509_PURPOSE_SMIME_SIGN, m2.X509_PURPOSE_ANY :
            if self.cert.check_purpose (purpose, 0) :
                self._status.append ("Signature purpose verified")
                break
        else :
            raise Signature_Error ("Signature purpose not verified")
        self.pubkey = self.cert.get_pubkey ().get_rsa ()
        self.verify_chain (self.cert)

        # FIXME: Check validity -- use which date?
        # FIXME: check CRL

        # expect also an M2Crypto.RSA.RSAError here and re-raise:
        try :
            if not self.pubkey.verify (self.digest, self.sig) :
                raise Signature_Error ("Signature not verified")
        except RSA.RSAError as cause :
            raise Signature_Error (cause)
        self._status.append \
            ("Good Signature from %s" % self.cert.get_subject ())
    # end def __init__

    @property
    def status (self) :
        return '\n'.join (self._status)
    # end def status

    def find_cert (self, name) :
        """ Find certificate by name in specified cert_location,
            raise Signature_Error if not found
        """
        hash = "%08x" % name.as_hash ()
        path = os.path.join (self.cert_location, hash)
        for ext in xrange (10) :
            try :
                cert = X509.load_cert ("%s.%s" % (path, ext))
                if cert.get_subject ().as_der () == name.as_der () :
                    return cert
            except IOError :
                pass
        else :
            raise Signature_Error ("Issuer Certificate not found")
    # end def find_cert

    def verify_chain (self, cert) :
        """ verify certificates with issuer, loop until we find a
            self-signed cert. From this extract crl url and try to do a
            CRL verify, too.
        """
        origcert = cert
        while True :
            subject     = cert.get_subject ()
            issuer      = cert.get_issuer  ()
            issuer_cert = self.find_cert (issuer)
            pubkey      = issuer_cert.get_pubkey ()
            if not cert.verify (pubkey) :
                raise Signature_Error \
                    ( "Certificate-Chain verify of %s with %s failed"
                    % (subject.as_text (), issuer.as_text ())
                    )
            self._status.append \
                ( "Certificate-Chain verify OK: %s with %s"
                % (subject.as_text (), issuer.as_text ())
                )
            if subject.as_der () == issuer.as_der () :
                break
            cert = issuer_cert
        # FIXME: How to verify the signature on the CRL?
        # FIXME: How to use the CRL??
        self.get_crl (issuer_cert)
    # end def verify_chain

    def get_crl (self, cert) :
        """ Get a Key revocation list from a cert """
        points = cert.get_ext ("crlDistributionPoints").get_value ()
        for url in points.split (',') :
            if not url.startswith ('URI:') :
                continue
            url = url [4:]
            # This should be wrapped in a try/except but I've had no
            # example yet where this fails. Then we should iterate over
            # all the URIs and select the one that opens.
            fh = m2urllib2.build_opener ().open (url)
        # Grmpf: M2Crypto doesn't wrap a method to create crl from DER
        # Grrmpf: And we need low-level methods, higher-level can only
        #         read from a file...
        # Grrrmpf: Hmm and how to use the CRL, then?
        crl_der = fh.read ()
        asn1 = der.decode (crl_der)
        print (asn1 [0][0])
        crl_pem = encodestring (crl_der)
        fh.close ()
        crl_pem = \
            '-----BEGIN X509 CRL-----\n%s-----END X509 CRL-----\n' % crl_pem
        bio = BIO.MemoryBuffer (crl_pem)
        cptr = m2.x509_crl_read_pem (bio.bio_ptr ())
        if cptr is None :
            raise Err.get_error ()
        crl = X509.CRL (cptr, 1)
        return crl
    # end def get_crl

# end class PDF_Signature

class PDF_Trodat_Signature :
    """
        XYZMO Seal formerly known as Trodat.
        Not fully implemented, the format is undocumented and XYZMO
        didn't send me instruction on how to verify this yet.
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
        print ("Catalog:", c)
        self.seal    = c ['/TRO_TrodatSeal'].getObject () [0].getObject ()
        assert (self.seal ['/Type'] == '/TRO_TrodatSealSignature')
        print ("Seal:", self.seal)
        pages        = c ['/Pages']
        print ("Kids:", pages ['/Kids'])
        content      = []
        for k in pages ['/Kids'] :
            print ("kid:", k.getObject ())
            print ("pdf:", k.pdf)
            content.append (k.getObject ())
        print (content)
        print ("Pages:", pages)
        labels       = c ['/PageLabels']
        print ("Labels:", labels)
        self.barcode = self.seal ['/BarCode'].getData ()
        xml          = self.seal ['/SecInfo'].getData ()
        self.xml     = ''.join (x for x in islice (xml, 0, None, 2))
        self.tree    = fromstring (self.xml)
        print ("SecInfo:", self.seal ['/SecInfo'])
        print ("\nXML:")
        print (self.xml)
        signator     = self.tree [0]
        assert (signator.tag == "signator")
        for node in signator :
            print ("%s: %s" % (node.tag, node.text), end = '')
            for k, v in node.attrib.iteritems () :
                print ("%s = %s " % (k, v), end = '')
            print ('')
        for c in "TSTInfo_Xml DocumentHash LtcSignature".split () :
            print (c)
            cert = b64decode (self.tree.find ('.//%s' % c).text)
            print (cert)
            for b in cert :
                print ("%02X " % ord (b), end = '')
            print ('')
            if c == "TSTInfo_Xml" :
                tsttree = fromstring ("<xml>" + cert + "</xml>")
                hm = b64decode (tsttree.find ('.//HashedMessage').text)
                print ("HashedMessage:")
                print (hm)
                for b in hm :
                    print ("%02X " % ord (b), end = '')
                print ('')
        for c in "LtcCertificate TSTInfo_Signature".split () :
            print (c)
            cert = self.tree.find ('.//%s' % c).text
            print (der.decode (b64decode (cert)))
    # end def __init__

# end class PDF_Trodat_Signature

if __name__ == "__main__" :
    #sig = PDF_Trodat_Signature \
    #    ("/home/ralf/200809171_HN_online_Schlatterbeck.pdf")
    sig = PDF_Signature \
        ( "/home/ralf/451719664-00.pdf"
        , "/home/ralf/checkout/own/projects/rsclib/rsclib/certs"
        )
    print (sig.status)
