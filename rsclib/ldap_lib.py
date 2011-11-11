#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import ldap

from ldap.cidict         import cidict
from ldap.controls       import SimplePagedResultsControl
from rsclib.autosuper    import autosuper

class LDAP_Search_Result (cidict, autosuper) :
    """ Wraps an LDAP search result.
        Noteworthy detail: We use an ldap.cidict for keeping the
        attributes, this is a case-insensitive dictionary variant.
    """
    def __init__ (self, vals) :
        assert (vals [0])
        self.dn = vals [0]
        dn = (x.split ('=') for x in self.dn.lower ().split (','))
        ou = dict.fromkeys (v.strip () for k, v in dn if k.strip () == 'ou')
        self.ou = ou
        self.__super.__init__ (vals [1])
    # end def __init__

    def __getattr__ (self, name) :
        if not name.startswith ('__') :
            try :
                result = self [name]
                setattr (self, name, result)
                return result
            except KeyError, cause :
                raise AttributeError, cause
        raise AttributeError, name
    # end def __getattr__
# end class LDAP_Search_Result

class LDAP_Query (autosuper) :

    page_size     = 50
    
    def __init__ \
        ( self
        , ldap_uri
        , bind_dn
        , password
        , base_dn   = ''
        , page_size = None
        , starttls  = False
        ) :
        self.base_dn   = base_dn
        self.page_size = page_size or self.page_size
        self.ldcon     = ldap.initialize (ldap_uri)
        self.ldcon.set_option (ldap.OPT_REFERRALS, 0)
        # try getting a secure connection, may want to force this later
        if starttls :
            try :
                    self.ldcon.start_tls_s ()
            except ldap.LDAPError, cause :
                pass
        # can raise an ldap.LDAPError:
        self.ldcon.simple_bind_s (bind_dn, password)
    # end def __init__

    def bind_as_user (self, username, password) :
        """ Bind as the given username/password -- useful to check
            authentication against the directory
        """
        luser = self.get_ldap_user_by_username (username)
        if not luser :
            return None
        try :
            self.ldcon.bind_s (luser.dn, password)
            return True
        except ldap.LDAPError, e :
            print >> sys.stderr, e
            pass
        return None
    # end def bind_as_user

    def get_all_ldap_usernames (self) :
        for r in self.paged_search_iter ('(objectclass=person)', ['uid']) :
            if 'uid' not in r :
                continue
            yield (r.uid [0]).lower ()
    # end def get_all_ldap_usernames

    def _get_ldap_user (self, result) :
        res = []
        for r in result :
            if r [0] :
                res.append (LDAP_Search_Result (r))
        assert (len (res) <= 1)
        if res :
            return res [0]
        return None
    # end def _get_ldap_user

    def get_ldap_user_by_username (self, username) :
        result = self.ldcon.search_s \
            ( self.base_dn
            , ldap.SCOPE_SUBTREE
            , '(uid=%s)' % username
            , None
            )
        return self._get_ldap_user (result)
    # end def get_ldap_user_by_username

    def get_ldap_user_by_dn (self, dn) :
        result = self.ldcon.search_s (dn, ldap.SCOPE_BASE)
        return self._get_ldap_user (result)
    # end def get_ldap_user_by_dn

    def paged_search_iter (self, filter, attrs = None) :
        lc = SimplePagedResultsControl \
            (ldap.LDAP_CONTROL_PAGE_OID, True, (self.page_size, ''))
        res = self.ldcon.search_ext \
            ( self.base_dn
            , ldap.SCOPE_SUBTREE
            , filter
            , attrlist    = attrs
            , serverctrls = [lc]
            )
        while True :
            rtype, rdata, rmsgid, serverctrls = self.ldcon.result3 (res)
            for r in rdata :
                if not r [0] :
                    continue
                r = LDAP_Search_Result (r)
                yield r
            pctrls = \
                [c for c in serverctrls
                   if c.controlType == ldap.LDAP_CONTROL_PAGE_OID
                ]
            if pctrls :
                x, cookie = pctrls [0].controlValue
                if not cookie :
                    break
                lc.controlValue = (self.page_size, cookie)
                res =  self.ldcon.search_ext \
                    ( self.base_dn
                    , ldap.SCOPE_SUBTREE
                    , filter
                    , attrs
                    , serverctrls = [lc]
                    )
            else :
                break
    # end def paged_search_iter

    def get_group (self, name, attr = 'cn', objectclass = 'groupOfNames') :
        f = '(&(%s=%s)(objectclass=%s))' % (attr, name, objectclass)
        l = self.ldcon.search_s (self.base_dn, ldap.SCOPE_SUBTREE, f)
        results = []
        for r in l :
            if not r [0] : continue
            r = LDAP_Search_Result (r)
            results.append (r)
        assert (len (results) == 1)
        r = results [0]
        self.members = dict.fromkeys (m.lower () for m in r.member)
    # end def get_group
# end class LDAP_Query
