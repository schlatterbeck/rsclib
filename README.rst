.. image:: http://sflogo.sourceforge.net/sflogo.php?group_id=212955&type=7
    :height: 62
    :width: 210
    :alt: SourceForge.net Logo
    :target: http://sourceforge.net/projects/rsclib

rsclib: Utility Routines
========================

:Author: Ralf Schlatterbeck <rsc@runtux.com>

The library includes various utility modules used in other projects.

 - ast_call: A simple call manager using asterisk: This can be used to
   originate a call and log all event associated to that call. So you
   can find out the status of the call and optionally the dialstatus.
 - ast_cdr: parser for CDR records in asterisk. We currently use
   text-files only, this might be later extended for database use.
 - ast_probe: Methods for checking for running asterisk
 - Autosuper magic (originally from Guido van Rossums announcement of
   Python 2.2): For refactoring it's a good idea that each class knows
   its parents (that the parent is not hardcoded in the upcall),
   achieved by adding a the __super attribute. Use as, e.g.,
   self.__super.method for calling method in the parent.
 - base_pickler: Allow to specify a dictionary of pickle exceptions, if
   the value in the dictionary is in __dict__ when pickle is called, the
   value in __dict__ is replaced with the value in the exception
   dictionary.
 - bero: A configurator for the `bero*fos`_ failover switch. See my
   `blogpost`_ why I wrote that (short summary: to work around bugs in
   the firmware of the device which are not addressed by the
   configurator code that comes with the device).
 - Config_File for python-syntax configuration files used in several of
   my projects.
 - crm: Tools for the cluster resource manager of the pacemaker high
   availability project. We allow querying of nodes, resources and
   errors for resources as well as resetting errors and migration of
   resources.
 - execute: module for executing commands and handling IO, this also
   has a Lock and a Log mixin. Now there is also a framework for
   executing processes in a pipeline, there can be fork-points in the
   pipeline where the output of one process feeds several pipelines.
   See test_exec.py and test2_exec.py.
 - ETree: wrapper around ElementTree for pretty-printing and xml export.
   This uses delegation (not inheritance) because we can't seem to
   inherit from ElementTree.
 - Firstname: given a string-candidate of a first name, check with
   popular web-site if it is really considered a first name. 
 - Freshmeat: Get project and release information via the freshmeat.net
   REST API. Also support submit of a new release. I'm now using this
   for announcing new releases for my projects.
 - grepmime: search for pattern in email attachments (even if these are
   encoded)
 - HTML_Parse for opening and parsing URLs. The class can be used to
   write a parser to extract info from a web page. After extraction the
   result can be pickled but we lose the ability to continue parsing
   after reading from the pickled result.
 - inductance: Inductance calculation of air-cored cylindrical
   flat-winded coil according to Robert Weaver
   http://electronbunker.ca/CalcMethods3b.html
 - IP_Address: IP v4 and v6 Addresses with subnet masking
 - iter_recipes: magic with iterators
 - isdn: model the status of Asterisk ISDN lines, either Linux Call
   Router (LCR) ISDN lines or lines managed by DAHDI. Special case for
   Xorcom modules which provide more information using Xorcom-specific
   files in /proc than native DAHDI modules.
 - ldap_lib: some routines for common ldap tasks including an iterator
   for LDAP implementations that use paged search (notably active
   directory).
 - Math implements Euclids algorithm for greatest common divisor and as
   a by-product the least common multiple
 - nmap: A parser for output of nmap scans to (e.g. to generate tables
   in TeX)
 - ocf: small framework for writing OCF scripts for the heartbeat
   cluster resource manager (probably also usable for the newer version
   called pacemaker but for now only tested with the version in Debian
   stable aka lenny).
 - PDF_Parse for opening and parsing PDFs, needs pdftotext installed
 - PDF_Signature: experimental code for checking signatures on adobe PDF
   documents
 - Phone: Parse phone numbers (Austria-specific)
 - PM_Value: Possibly missing value, encapsulate a number which may be
   missing and associated arithmetics.
 - Rational: Implementation of Rational numbers
 - stateparser: Simple state-machine parser class, this is used for
   writing line-based parsers using a state machine. For an example
   usage see nmap. After parsing the result can be pickled but we lose
   the ability to continue parsing after reading from the pickled
   result.
 - sqlparser: Parse SQL dumps from postgreSQL and mysql
 - timeout: A simple timeout mechanism using SIGALRM
 - Tex_CSV_Writer: Write CVS files in a syntax that can be parsed by
   TeX. Implements same interface as the csv module. Only implements
   writing.
 - trafficshape: Simple traffic shaping configuration: Currently
   generates Linux tc commands for a traffic shaping config using hfsc
   for shaping and sfq or red for the leaf qdiscs. We also provide a
   translator from iptables mangle rules (for traffic marking) to tc
   commands for filtering. This is needed if we want to do inbound
   shaping. The Linux kernel doesn't support inbound shaping, so we need
   to redirect all traffic to an ifb device. On that device we do
   *outbound* shaping. Unfortunately when sending traffic to an ifb
   device with a tc filter + action mirred command this occurs *before*
   the PREROUTING chain. This means packets are not yet marked. So we
   provide a parser to translate mangle rules in the PREROUTING chain to
   appropriate tc commands. For implementing this we mark packets (using
   the tc action xt (formerly known as ipt used for iptables marking, a
   backward-compatibility option can be used) in the original device and
   then use the marked information in the ifb device to send the traffic
   to appropriate qdiscs. This supports a two-level approach: Rules in
   iptables that match on a packet mark (using --mark) are translated to
   tc commands in the ifb device (they depend on the mark already
   present). All other rules are translated to a tc action xt (using -j
   MARK) and a tc action mirred redirect (for sending the traffic to the
   ifb device) for the *original* device (e.g. eth0 redirecting to
   ifb0). The PREROUTING commands by default are directly taken from the
   running kernel by default (using "iptables -t mangle -S -v")

.. _`bero*fos`: https://shop.beronet.com/product_info.php/cPath/56/products_id/159
.. _`blogpost`: http://blog.runtux.com/2009/04/09/81/

Resources
---------

Download the source at https://sourceforge.net/projects/rsclib/
and install using the standard python setup, e.g.::

 python setup.py install --prefix=/usr/local

Alternatively get it from pypi and/or install via pip.


Changes
-------

Version 0.47: Fixes for IP_Address; pypi

   - IP_Address: Relax inheritance checks when comparing IP_Address
     instances
   - Version uploaded to pypi and documented in README

Version 0.46: Additions to ast_probe; Bug-fix

   - ast_probe now has methods for checking sip registry and reloading
     the sip subsystem in asterisk
   - Add a small script, ast_sip_check for checking sip registration on
     an asterisk server and restart sip if some registrations are
     missing.
   - Config_File fixes the __getattr_ method to return an
     AttributeError in case of failure

Version 0.45: Fix ISDN ports

String reprentation had leading unicode 'u'

   - Fix string representation in ISDN ports

Version 0.44: Make line-waiting for bero configurable

For cluster resource berofos we make waiting for the L1 and L2 of the
ISDN line configurable. The hard-coded default was too low.

   - New config-item ISDN_WAIT_UP

Version 0.43: Support new berofos firmware

The new berofos (failover switch) firmware has some new low-level
commands which we now accept when getting the device status.

  - Fix bero.py to accept new low-level commands
  - Add some more documentation to bero.py
  - Add description of ast_probe in this README

Version 0.42: Feature enhancements

Add crm for pacemaker cluster management, new ast_probe for checking of
asterisk status. Fixes to ocf and ast_call.

  - Add crm.py
  - Add ast_probe.py
  - Allow specification of parsed config (cfg) for Call_Manager in
    ast_call.py
  - Better resource monitoring for asterisk and dahdi in ocf.py
  - fix ocf.py to use new classes in isdn.py
  - isdn.py now doesn't probe asterisk for the isdn stack in use if it
    finds a hint in the config-file

Version 0.41: Minor feature enhancements

Fixes to Freshmeat, pycompat, sql-dump parser.

  - Fix parsing of escaped quotes in mysql dumps
  - Freshmeat
  - pycompat fixes

Version 0.40: Distribution bug-fix

Renaming of README lead to the missing file README.rst in the distro.

  - Fix MANIFEST.in

Version 0.39: Minor feature enhancements

Fixes to hexdump, unicode issues (elementtree wrapper, stateparser).
Add some fixes to IP_Address comparison. The nmap output has changed in
recent versions, adapt to new format.

  - Make address in hexdump configurable
  - Bug-fix with comparison of sub-classes in IP_Address
  - Unicode support in ETree
  - Unicode support in stateparser
  - Fix for trailing empty attributes in CSV output of PostgreSQL dumps
    in sqlparser
  - Unicode support in sqlparser (uses stateparser)
  - Parse new nmap format
  - Fix for configurable Releasetools location

Version 0.38: Minor feature enhancements

Fix boolean conversion of IP6_Address (and IP4_Address).

 - IP6_Address would throw an error when trying a truth-test. Add
   __nonzero__ (which always returns True even for the 0 Address)

Version 0.37: Minor feature enhancements

Change sort-order of IP_Address, make IP_Address immutable, use
metaclass magic to allow copy-constructor semantics.

 - Sort order of IP_Address objects (both v4 and v6) now reverses the
   order of the netmask: If the IP-Address part of the objects to
   compare are the same, we used to sort by *inverse* netmask (putting
   smaller networks with higher netmask first). We now reversed this to
   be compatible with PostgrSQL cidr type objects.
 - All attributes of IP_Address objects are now implemented as
   properties to return the '_' variant of the attribute. Thus
   IP_Address objects are (when using the public interface) immutable.
   Since we already had a __hash__ method this effectively fixes the
   interface to not allow mutation of objects that are in a dictionary.
 - Allow calling the IP_Address constructors with another IP_Address
   object. Since IP_Address objects are now immutable we use metaclass
   trickery to return the passed object itself (instead of generating a
   copy).

Version 0.36: Minor feature enhancements

Allow auto-coercion of comparison parameters. Add parent property and
is_sibling test.

 - Now comparison operators and 'in' do auto coercion.
 - Add parent property (next bigger network)
 - Add is_sibling test (same parent)

Version 0.35: Minor feature enhancements

Add 'mask_len' as an alias of 'mask' to IP_Address.

 - Need the network mask length (aka prefix length) sometimes as
   mask_len (e.g. for FFM on github).

Version 0.34: Minor feature enhancements

Fix trafficshape to use new tc syntax. Add label to hexdump.

 - The tc command has renamed the ``ipt`` action to ``xt`` (Linux
   introduced xtables as a refactoring of iptables), the old ``ipt`` is
   still available in ``iproute2`` but we make ``xt`` the default now.
   A backward-compatibility parameter can be used to get the old
   behavior.
 - Add save-mark to iptables action parser.
 - The hexdump class now can generate labels.

Version 0.33: Minor feature enhancements

More fixes for ast_call.

 - Add parser for events from asterisk wireshark trace
 - Add fail.log for 'real' test
 - Don't double-register call with Call_Manager
 - Allow explicit matching by account-code

Version 0.32: Minor feature enhancements

More fixes for ast_call.

 - Regression test with pyst asterisk emulator
 - Fix case where OriginateResponse immediately returns Failure
 - Tests for cases where Hangup comes before or after the
   OriginateResponse

Version 0.31: Minor feature enhancements

Fix ast_call for immediately failing calls. Fix dahdi channel
computation in isdn.py.

 - Fix OriginateResponse handling in ast_call
 - Fix dahdi channel computation, can't directly use the span, use the
   basechan attribute

Version 0.30: Minor feature enhancements

Fix how dahdi vs. mISDN interpret what is called an interface and what
is called a port. In mISDN we can combine several ports (physical lines)
to an interface. In dahdi both are the same (a port is a span in dahdi).

 - Remove parsing of B- and C- channels from dahdi isdn parser

Version 0.29: Minor feature enhancements

The lcr module is now named isdn. It can now handle isdn interfaces
managed by Asterisk DAHDI in addition to Linux Call Router (LCR).

Version 0.28: Minor feature enhancements

Fix inductance formula of Robert Weaver, thanks Robert for pointing me
to the correction you did on your new site! For most doctests in the
inductance module the error was in the lower percentage points.
Add an xxrange iterator to the iter_recipes that can replace pythons
native xrange iterator but works with long integers. Needed for some
operations on IPv6 addresses in the IP_Address module.

 - Fix inductance calculation according to patch from Robert Weaver
 - Add xxrange iterator to iter_recipes
 - Use new xxrange instead of xrange in IP_Address module, add a test
   that failed with large numbers for IPv6

Version 0.27: Minor feature enhancements

Add pageurl and pageinfo attributes to HTML_Parser.Page_Tree, other
enhancements to HTML_Parser. Add pickle support to parser classes.
Fix comparison of IP_Address classes.

 - Add pageurl and pageinfo attributes to HTML_Parser.Page_Tree storing
   information retrieved via geturl and info calls from urllib2.
 - Parser classes in stateparser.py and HTML_Parse.py where not
   pickleable, fixed by removing parser-specific attributes when calling
   pickle. Note that the parsing cannot be continued after reading class
   from a pickle.
 - Add base_pickler module to allow pickle exceptions
 - HTML_Parse: Make Parse_Error a ValueError
 - HTML_Parse: Raise line number with exception
 - HTML_Parse: Add a timeout
 - HTML_Parse: raise Retries_Exceeded with url
 - HTML_Parse: url parameter may now be None, not joined with site
   parameter
 - Add pageurl and pageinfo to HTML_Parse
 - IP_Address: Fix comparison
 - Slight refactoring of NMAP_Parser class

Version 0.26: Minor feature enhancements

Fix double-utf-8-encoding option for sqlparser. Enhance stderr handling
for exec_pipe.

 - More detected broken encodings for fix_double_encode option
 - execute.py: add error message from executed command to message raised
   by exec_pipe, make stderr output available in non-failing case.

Version 0.25: Minor feature enhancements

Add sqlparser for parsing SQL dumps of PostgreSQL and mysql, add Phone
to parse phone numbers.

 - sqlparser added
 - Phone added for parsing phone numbers

Version 0.24: Minor feature enhancements

Better syntax checks and comparison operators for IP_Address, bug fixes
for parser and __str__ for IP_Address.IP6_Address

 - IP_Address better syntax checks
 - IP_Address __cmp__ and __eq__ improved for comparison with other types
 - more regression tests for IP6_Address
 - bug fixes in __str__ and parser of IP6_Address
 - support for strict checking of netmask (all bits at right of netmask
   must be zero if strict_mask is True)

Version 0.23: Minor feature enhancements

IP4_Address can now be put in a dict, add a subnets iterator for
IP4_Address. Factor IP_Address and add IP6_Address

 - Add __hash__ for IP_Address
 - The new subnets iterator for IP_Address iterates over all IPs in a
   subnet. Optionally a netmask can be specified.
 - Support for IPv6 addresses
 - rename IP4_Address to IP_Address

Version 0.22: Minor feature enhancements

Allow unicode ip address input, hopefully make rsclib installable via pip.

 - Address given to IP4_Address constructor now may be unicode
 - Add download_url to setup.py to make installable via pip

Version 0.21: Minor feature enhancements

Fix autosuper: allow to inherit from non-autosuper classes, some small
fixes to ast_call and lcr parser. Fix ETree pretty-printing. Update
Freshmeat to new hostname. Add dotted netmaks parsing to IP4_Address.

 - Since python2.6 constructor of "object" do not allow parameters, so
   we need to strip these when doing the upcall from autosuper. This
   fails when e.g. inheriting from a non-autosuper enabled class, e.g.,
   class (With_Autosuper, dict)
   in that case dict would get empty parameters. New implementation
   finds out if our upcall is to "object", only in that case strip
   parameters.
 - ast_call now processes all queued unhandled events when a call is
   matched.
 - update regression test for ast_call.Call
 - lcr parser: fix regex, port can have an empty name.
 - Optimize call matching in ast_call: mark call as closed once we are
   sure about the uniqueid. Add matching of Account-Code.
 - Fix ETree pretty-printing: don't print unicode strings when arguments
   are already converted
 - freshmeat.net now is freecode.com (and the API redirects there),
   update Freshmeat.py to new hostname (including .netrc credentials
   with compatibility for old name).
 - explicit mask paramter of IP4_Address can now be a dotted netmask.

Version 0.20: Not announced on freshmeat

Database value output for ast_cdr, added inductance calculation.

 - ast_cdr: Add methods for database values of CDR records -- database
   values of CDRs are different, they don't include start, end, answer
   time-stamps but instead only a calldate, in addition the amaflags are
   numerical in the database.
 - added inductance calculation

Version 0.19: Not announced on freshmeat

Extend ETree with a walk method and implement small ldap library

 - ETree: add walk method to walk the tree and call an optional pre- and
   post-hook function
 - ldap_lib: common ldap tasks for user and group search, and an
   iterator for paged search (used with active directory).

Version 0.18: Not announced on freshmeat

Bugfix of ast_call and update for asterisk 1.6, small extension to
IP4_Address.

 - ast_call: match calls via (unique) account code
 - ast_call: State vs ChannelState parameter in Newstate event
 - ast_call: handle immediate error from asterisk (e.g. Permission Denied)
 - IP4_Address: add netblk (start and end address for address with
   netmask)

Version 0.17: Not announced on freshmeat

Factor ETree (extended ElementTree) from HTML_Parse. New Freshmeat
module to get project information and submit new releases via the new
freshmeat REST API. New simple hexdump module.

 - New ETree.py (extended ElementTree)
 - New Freshmeat.py
 - New hexdump.py
 - adapt lcr module to new version of Linux Call Router

Version 0.16: Not announced on freshmeat

Add an iptables to tc translator for translating mangle rules in the
iptables PREROUTING chain to appropriate tc commands (using an ipt
action and mirred redirect actions).

 - Add iptables to tc translator to trafficshape.py

Version 0.15: Not announced on freshmeat

Add a framework for traffic shaping with linux iproute (tc). Minor
updates to iter_recipes.

 - Initial implementation of trafficshape.py
 - Add iter_recipes.combinations from python2.6 manpage of itertools
   for backward compatibility

Version 0.14: Not announced on freshmeat

Add a framework for process pipeline execution, processes can either be
python methods or external programs (with parameter list).  They can be
connected in a pipe and there may be T-points in the pipe, where the
pipe forks into two or more pipelines fed by the output of one process.

 - Add process pipeline framework
 - HTML_Parse now has an explicit translate hook for preprocessing the
   html page before parsing it. This defaults to the old behaviour of
   filtering out common characters in broken HTML.
 - Add nmap parser (e.g. to generate TeX tables from an nmap scan)
 - Fix Lock_Mixin in execute module to remove lockfile at exit,
   this used to rely on __del__ which breaks in certain cases.
 - add file upload to HTML_Parse

Version 0.13: Not announced on freshmeat

Bug-Fix Release: Fix signal handler in timeout.py

 - fix signal handler timeout.py

Version 0.12: Not announced on freshmeat

Add a simple timeout mechanism using SIGALRM.

 - add timeout.py

Version 0.11: Not announced on freshmeat

Add a parser for CDR records in asterisk. We currently use text-files
only, this might be later extended for database use. Some fixes for
ast_call, make call-handling more robust (some race conditions would
identify events of other calls as belonging to our initiated call).
Add an execute module for executing commands and handling IO, this also
has a Lock and a Log mixin. Add ocf.py, a small framework for writing
OCF scripts for the heartbeat cluster resource manager (probably also
usable for the newer version called pacemaker but for now only tested
with the version in Debian stable aka lenny). Add lcr.py to model the
status of Linux Call Router ISDN lines.

 - add ast_cdr.py
 - fix ast_call.py
 - fix up-chaining in stateparser.py
 - add execute.py
 - add ocf.py
 - add lcr.py

Version 0.10: Not announced on freshmeat

add ast_call for asterisk auto-dialling, small fixes to IP4_Address, add
bero*fos configurator, experimental code for checking PDF signature

 - add ast_call.py
 - Firstname: don't look up names with len < 2
 - IP4_Address: some aliases for common functions
 - IP4_Address: add __cmp__
 - bero.py: bero*fos configurator
 - HTML_Parse updated for python 2.5
 - stateparser update: use self.matrix by default
 - PDF_Signature: experimental code for checking signatures on adobe PDF
   documents
 - iter_recipes: some magic with iterators

Version 0.9: Not announced on freshmeat

Add binom to the Math package, add Firstname, Bug-Fix Release Rational

 - binom (n, m) computes the binomial coefficient of n, m.
 - Firstname: check if candidate is a first name candidate according to
   popular web site.
 - Rational: On division we could get a negative denominator -- fixed
 - make Config_File a descendent of autosuper

Version 0.8: Not announced on freshmeat

Added more documentation.
State-machine parser stateparser implemented. Rational number arithmetic
package added.

 - stateparser implemented (simple state-machine line-oriented
   configurable parser)
 - usage-example of IP4_Address prints debian /etc/network/interfaces
   entry.
 - Math added (Euclids algorithm, gcd, lcm)
 - Rational number arithmetics
 - cookie processing for HTML_Parse
 - basic HTML auth for HTML_Parse
 - HTML_Parse: move to urllib2

Version 0.7: Not announced on freshmeat

Small Python library with various things such as Configuration file
parsing (in Python syntax), HTML and PDF parsing.

 - First Release version
