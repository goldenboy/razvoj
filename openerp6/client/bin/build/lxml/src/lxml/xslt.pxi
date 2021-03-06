# XSLT

cimport xslt

class XSLTError(LxmlError):
    u"""Base class of all XSLT errors.
    """
    pass

class XSLTParseError(XSLTError):
    u"""Error parsing a stylesheet document.
    """
    pass

class XSLTApplyError(XSLTError):
    u"""Error running an XSL transformation.
    """
    pass

class XSLTSaveError(XSLTError):
    u"""Error serialising an XSLT result.
    """
    pass

class XSLTExtensionError(XSLTError):
    u"""Error registering an XSLT extension.
    """
    pass

# version information
LIBXSLT_COMPILED_VERSION = __unpackIntVersion(xslt.LIBXSLT_VERSION)
LIBXSLT_VERSION = __unpackIntVersion(xslt.xsltLibxsltVersion)


################################################################################
# Where do we store what?
#
# xsltStylesheet->doc->_private
#    == _XSLTResolverContext for XSL stylesheet
#
# xsltTransformContext->_private
#    == _XSLTResolverContext for transformed document
#
################################################################################


################################################################################
# XSLT document loaders

cdef class _XSLTResolverContext(_ResolverContext):
    cdef xmlDoc* _c_style_doc
    cdef _BaseParser _parser

    cdef _XSLTResolverContext _copy(self):
        cdef _XSLTResolverContext context
        context = _XSLTResolverContext()
        _initXSLTResolverContext(context, self._parser)
        context._c_style_doc = self._c_style_doc
        return context

cdef _initXSLTResolverContext(_XSLTResolverContext context,
                              _BaseParser parser):
    _initResolverContext(context, parser.resolvers)
    context._parser = parser
    context._c_style_doc = NULL

cdef xmlDoc* _xslt_resolve_from_python(char* c_uri, void* c_context,
                                       int parse_options, int* error) with gil:
    # call the Python document loaders
    cdef _XSLTResolverContext context
    cdef _ResolverRegistry resolvers
    cdef _InputDocument doc_ref
    cdef xmlDoc* c_doc

    error[0] = 0
    context = <_XSLTResolverContext>c_context

    # shortcut if we resolve the stylesheet itself
    c_doc = context._c_style_doc
    if c_doc is not NULL and c_doc.URL is not NULL:
        if cstd.strcmp(c_uri, c_doc.URL) == 0:
            return _copyDoc(c_doc, 1)

    # delegate to the Python resolvers
    try:
        resolvers = context._resolvers
        if cstd.strncmp('string://', c_uri, 9) == 0:
            uri = _decodeFilename(c_uri + 9)
            if cstd.strncmp('string://', context._c_style_doc.URL, 9) != 0 and \
                    cstd.strcmp('<string>', context._c_style_doc.URL) != 0:
                # stylesheet URL known => make the target URL absolute
                uri = os_path_join(_decodeFilename(context._c_style_doc.URL), uri)
        else:
            uri = _decodeFilename(c_uri)
        doc_ref = resolvers.resolve(uri, None, context)

        c_doc = NULL
        if doc_ref is not None:
            if doc_ref._type == PARSER_DATA_STRING:
                c_doc = _parseDoc(
                    doc_ref._data_bytes, doc_ref._filename, context._parser)
            elif doc_ref._type == PARSER_DATA_FILENAME:
                c_doc = _parseDocFromFile(doc_ref._filename, context._parser)
            elif doc_ref._type == PARSER_DATA_FILE:
                c_doc = _parseDocFromFilelike(
                    doc_ref._file, doc_ref._filename, context._parser)
            elif doc_ref._type == PARSER_DATA_EMPTY:
                c_doc = _newXMLDoc()
            if c_doc is not NULL and c_doc.URL is NULL:
                c_doc.URL = tree.xmlStrdup(c_uri)
        return c_doc
    except:
        context._store_raised()
        error[0] = 1
        return NULL

cdef void _xslt_store_resolver_exception(char* c_uri, void* context,
                                         xslt.xsltLoadType c_type) with gil:
    try:
        message = u"Cannot resolve URI %s" % _decodeFilename(c_uri)
        if c_type == xslt.XSLT_LOAD_DOCUMENT:
            exception = XSLTApplyError(message)
        else:
            exception = XSLTParseError(message)
        (<_XSLTResolverContext>context)._store_exception(exception)
    except Exception, e:
        (<_XSLTResolverContext>context)._store_exception(e)

cdef xmlDoc* _xslt_doc_loader(char* c_uri, tree.xmlDict* c_dict,
                              int parse_options, void* c_ctxt,
                              xslt.xsltLoadType c_type) nogil:
    # no Python objects here, may be called without thread context !
    # when we declare a Python object, Pyrex will INCREF(None) !
    cdef xmlDoc* c_doc
    cdef xmlDoc* result
    cdef void* c_pcontext
    cdef int error
    # find resolver contexts of stylesheet and transformed doc
    if c_type == xslt.XSLT_LOAD_DOCUMENT:
        # transformation time
        c_pcontext = (<xslt.xsltTransformContext*>c_ctxt)._private
    elif c_type == xslt.XSLT_LOAD_STYLESHEET:
        # include/import resolution while parsing
        c_pcontext = (<xslt.xsltStylesheet*>c_ctxt).doc._private
    else:
        c_pcontext = NULL

    if c_pcontext is NULL:
        # can't call Python without context, fall back to default loader
        return XSLT_DOC_DEFAULT_LOADER(
            c_uri, c_dict, parse_options, c_ctxt, c_type)

    c_doc = _xslt_resolve_from_python(c_uri, c_pcontext, parse_options, &error)
    if c_doc is NULL and not error:
        c_doc = XSLT_DOC_DEFAULT_LOADER(
            c_uri, c_dict, parse_options, c_ctxt, c_type)
        if c_doc is NULL:
            _xslt_store_resolver_exception(c_uri, c_pcontext, c_type)

    if c_doc is not NULL and c_type == xslt.XSLT_LOAD_STYLESHEET:
        c_doc._private = c_pcontext
    return c_doc

cdef xslt.xsltDocLoaderFunc XSLT_DOC_DEFAULT_LOADER
XSLT_DOC_DEFAULT_LOADER = xslt.xsltDocDefaultLoader

xslt.xsltSetLoaderFunc(_xslt_doc_loader)

################################################################################
# XSLT file/network access control

cdef class XSLTAccessControl:
    u"""XSLTAccessControl(self, read_file=True, write_file=True, create_dir=True, read_network=True, write_network=True)

    Access control for XSLT: reading/writing files, directories and
    network I/O.  Access to a type of resource is granted or denied by
    passing any of the following boolean keyword arguments.  All of
    them default to True to allow access.

    - read_file
    - write_file
    - create_dir
    - read_network
    - write_network

    For convenience, there is also a class member `DENY_ALL` that
    provides an XSLTAccessControl instance that is readily configured
    to deny everything, and a `DENY_WRITE` member that denies all
    write access but allows read access.

    See `XSLT`.
    """
    cdef xslt.xsltSecurityPrefs* _prefs
    def __init__(self, *, read_file=True, write_file=True, create_dir=True,
                 read_network=True, write_network=True):
        self._prefs = xslt.xsltNewSecurityPrefs()
        if self._prefs is NULL:
            python.PyErr_NoMemory()
        self._setAccess(xslt.XSLT_SECPREF_READ_FILE, read_file)
        self._setAccess(xslt.XSLT_SECPREF_WRITE_FILE, write_file)
        self._setAccess(xslt.XSLT_SECPREF_CREATE_DIRECTORY, create_dir)
        self._setAccess(xslt.XSLT_SECPREF_READ_NETWORK, read_network)
        self._setAccess(xslt.XSLT_SECPREF_WRITE_NETWORK, write_network)

    DENY_ALL = XSLTAccessControl(
        read_file=False, write_file=False, create_dir=False,
        read_network=False, write_network=False)

    DENY_WRITE = XSLTAccessControl(
        read_file=True, write_file=False, create_dir=False,
        read_network=True, write_network=False)

    def __dealloc__(self):
        if self._prefs is not NULL:
            xslt.xsltFreeSecurityPrefs(self._prefs)

    cdef _setAccess(self, xslt.xsltSecurityOption option, allow):
        cdef xslt.xsltSecurityCheck function
        if allow:
            function = xslt.xsltSecurityAllow
        else:
            function = xslt.xsltSecurityForbid
        xslt.xsltSetSecurityPrefs(self._prefs, option, function)

    cdef void _register_in_context(self, xslt.xsltTransformContext* ctxt):
        xslt.xsltSetCtxtSecurityPrefs(self._prefs, ctxt)

    property options:
        u"The access control configuration as a map of options."
        def __get__(self):
            return {
                u'read_file': self._optval(xslt.XSLT_SECPREF_READ_FILE),
                u'write_file': self._optval(xslt.XSLT_SECPREF_WRITE_FILE),
                u'create_dir': self._optval(xslt.XSLT_SECPREF_CREATE_DIRECTORY),
                u'read_network': self._optval(xslt.XSLT_SECPREF_READ_NETWORK),
                u'write_network': self._optval(xslt.XSLT_SECPREF_WRITE_NETWORK),
                }

    cdef _optval(self, xslt.xsltSecurityOption option):
        cdef xslt.xsltSecurityCheck function
        function = xslt.xsltGetSecurityPrefs(self._prefs, option)
        if function is <xslt.xsltSecurityCheck>xslt.xsltSecurityAllow:
            return True
        elif function is <xslt.xsltSecurityCheck>xslt.xsltSecurityForbid:
            return False
        else:
            return None

    def __repr__(self):
        items = self.options.items()
        items.sort()
        return u"%s(%s)" % (
            funicode(python._fqtypename(self)).split(u'.')[-1],
            u', '.join([u"%s=%r" % item for item in items]))

################################################################################
# XSLT

cdef int _register_xslt_function(void* ctxt, name_utf, ns_utf):
    if ns_utf is None:
        return 0
    return xslt.xsltRegisterExtFunction(
        <xslt.xsltTransformContext*>ctxt, _cstr(name_utf), _cstr(ns_utf),
        _xpath_function_call)

cdef int _unregister_xslt_function(void* ctxt, name_utf, ns_utf):
    if ns_utf is None:
        return 0
    return xslt.xsltRegisterExtFunction(
        <xslt.xsltTransformContext*>ctxt, _cstr(name_utf), _cstr(ns_utf),
        NULL)


cdef class _XSLTContext(_BaseContext):
    cdef xslt.xsltTransformContext* _xsltCtxt
    cdef object _extension_elements
    cdef _ReadOnlyElementProxy _extension_element_proxy
    def __init__(self, namespaces, extensions, enable_regexp,
                 build_smart_strings):
        self._xsltCtxt = NULL
        self._extension_elements = EMPTY_READ_ONLY_DICT
        if extensions is not None and extensions:
            for ns_name_tuple, extension in extensions.items():
                if ns_name_tuple[0] is None:
                    raise XSLTExtensionError, \
                        u"extensions must not have empty namespaces"
                if isinstance(extension, XSLTExtension):
                    if self._extension_elements is EMPTY_READ_ONLY_DICT:
                        self._extension_elements = {}
                        extensions = python.PyDict_Copy(extensions)
                    ns_utf   = _utf8(ns_name_tuple[0])
                    name_utf = _utf8(ns_name_tuple[1])
                    python.PyDict_SetItem(
                        self._extension_elements, (ns_utf, name_utf),
                        extension)
                    python.PyDict_DelItem(extensions, ns_name_tuple)
        _BaseContext.__init__(self, namespaces, extensions, enable_regexp,
                              build_smart_strings)

    cdef _BaseContext _copy(self):
        cdef _XSLTContext context
        context = <_XSLTContext>_BaseContext._copy(self)
        context._extension_elements = self._extension_elements
        return context

    cdef register_context(self, xslt.xsltTransformContext* xsltCtxt,
                               _Document doc):
        self._xsltCtxt = xsltCtxt
        self._set_xpath_context(xsltCtxt.xpathCtxt)
        self._register_context(doc)
        self.registerLocalFunctions(xsltCtxt, _register_xslt_function)
        self.registerGlobalFunctions(xsltCtxt, _register_xslt_function)
        _registerXSLTExtensions(xsltCtxt, self._extension_elements)

    cdef free_context(self):
        self._cleanup_context()
        self._release_context()
        if self._xsltCtxt is not NULL:
            xslt.xsltFreeTransformContext(self._xsltCtxt)
            self._xsltCtxt = NULL
        self._release_temp_refs()


cdef class XSLT:
    u"""XSLT(self, xslt_input, extensions=None, regexp=True, access_control=None)

    Turn an XSL document into an XSLT object.

    Calling this object on a tree or Element will execute the XSLT::

      >>> transform = etree.XSLT(xsl_tree)
      >>> result = transform(xml_tree)

    Keyword arguments of the constructor:

    - extensions: a dict mapping ``(namespace, name)`` pairs to
      extension functions or extension elements
    - regexp: enable exslt regular expression support in XPath
      (default: True)
    - access_control: access restrictions for network or file
      system (see `XSLTAccessControl`)

    Keyword arguments of the XSLT call:

    - profile_run: enable XSLT profiling (default: False)

    Other keyword arguments of the call are passed to the stylesheet
    as parameters.
    """
    cdef _XSLTContext _context
    cdef xslt.xsltStylesheet* _c_style
    cdef _XSLTResolverContext _xslt_resolver_context
    cdef XSLTAccessControl _access_control
    cdef _ErrorLog _error_log

    def __init__(self, xslt_input, *, extensions=None, regexp=True,
                 access_control=None):
        cdef xslt.xsltStylesheet* c_style
        cdef xmlDoc* c_doc
        cdef _Document doc
        cdef _Element root_node

        doc = _documentOrRaise(xslt_input)
        root_node = _rootNodeOrRaise(xslt_input)

        # set access control or raise TypeError
        self._access_control = access_control

        # make a copy of the document as stylesheet parsing modifies it
        c_doc = _copyDocRoot(doc._c_doc, root_node._c_node)

        # make sure we always have a stylesheet URL
        if c_doc.URL is NULL:
            doc_url_utf = python.PyUnicode_AsASCIIString(
                u"string://__STRING__XSLT__%d" % id(self))
            c_doc.URL = tree.xmlStrdup(_cstr(doc_url_utf))

        self._error_log = _ErrorLog()
        self._xslt_resolver_context = _XSLTResolverContext()
        _initXSLTResolverContext(self._xslt_resolver_context, doc._parser)
        # keep a copy in case we need to access the stylesheet via 'document()'
        self._xslt_resolver_context._c_style_doc = _copyDoc(c_doc, 1)
        c_doc._private = <python.PyObject*>self._xslt_resolver_context

        self._error_log.connect()
        with nogil:
            c_style = xslt.xsltParseStylesheetDoc(c_doc)
        self._error_log.disconnect()

        if c_style is NULL:
            tree.xmlFreeDoc(c_doc)
            self._xslt_resolver_context._raise_if_stored()
            # last error seems to be the most accurate here
            if self._error_log.last_error is not None and \
                    self._error_log.last_error.message:
                raise XSLTParseError(self._error_log.last_error.message,
                                     self._error_log)
            else:
                raise XSLTParseError(
                    self._error_log._buildExceptionMessage(
                        u"Cannot parse stylesheet"),
                    self._error_log)

        c_doc._private = NULL # no longer used!
        self._c_style = c_style
        self._context = _XSLTContext(None, extensions, regexp, True)

    def __dealloc__(self):
        if self._xslt_resolver_context is not None and \
               self._xslt_resolver_context._c_style_doc is not NULL:
            tree.xmlFreeDoc(self._xslt_resolver_context._c_style_doc)
        # this cleans up the doc copy as well
        xslt.xsltFreeStylesheet(self._c_style)

    property error_log:
        u"The log of errors and warnings of an XSLT execution."
        def __get__(self):
            return self._error_log.copy()

    def apply(self, _input, *, profile_run=False, **kw):
        u"""apply(self, _input,  profile_run=False, **kw)
        
        :deprecated: call the object, not this method."""
        return self(_input, profile_run=profile_run, **kw)

    def tostring(self, _ElementTree result_tree):
        u"""tostring(self, result_tree)

        Save result doc to string based on stylesheet output method.

        :deprecated: use str(result_tree) instead.
        """
        return str(result_tree)

    def __deepcopy__(self, memo):
        return self.__copy__()

    def __copy__(self):
        return _copyXSLT(self)

    def __call__(self, _input, *, profile_run=False, **kw):
        u"""__call__(self, _input, profile_run=False, **kw)

        Execute the XSL transformation on a tree or Element.

        Pass the ``profile_run`` option to get profile information
        about the XSLT.  The result of the XSLT will have a property
        xslt_profile that holds an XML tree with profiling data.
        """
        cdef _XSLTContext context
        cdef _XSLTResolverContext resolver_context
        cdef _Document input_doc
        cdef _Element root_node
        cdef _Document result_doc
        cdef _Document profile_doc
        cdef xmlDoc* c_profile_doc
        cdef xslt.xsltTransformContext* transform_ctxt
        cdef xmlDoc* c_result
        cdef xmlDoc* c_doc
        cdef tree.xmlDict* c_dict

        input_doc = _documentOrRaise(_input)
        root_node = _rootNodeOrRaise(_input)

        c_doc = _fakeRootDoc(input_doc._c_doc, root_node._c_node)

        transform_ctxt = xslt.xsltNewTransformContext(self._c_style, c_doc)
        if transform_ctxt is NULL:
            _destroyFakeDoc(input_doc._c_doc, c_doc)
            python.PyErr_NoMemory()

        initTransformDict(transform_ctxt)

        if profile_run:
            transform_ctxt.profile = 1

        try:
            self._error_log.connect()
            context = self._context._copy()
            context.register_context(transform_ctxt, input_doc)

            resolver_context = self._xslt_resolver_context._copy()
            transform_ctxt._private = <python.PyObject*>resolver_context

            c_result = self._run_transform(
                c_doc, kw, context, transform_ctxt)

            if transform_ctxt.state != xslt.XSLT_STATE_OK:
                if c_result is not NULL:
                    tree.xmlFreeDoc(c_result)
                    c_result = NULL

            if transform_ctxt.profile:
                c_profile_doc = xslt.xsltGetProfileInformation(transform_ctxt)
                if c_profile_doc is not NULL:
                    profile_doc = _documentFactory(
                        c_profile_doc, input_doc._parser)
        finally:
            if context is not None:
                context.free_context()
            _destroyFakeDoc(input_doc._c_doc, c_doc)
            self._error_log.disconnect()

        try:
            if resolver_context is not None and resolver_context._has_raised():
                if c_result is not NULL:
                    tree.xmlFreeDoc(c_result)
                    c_result = NULL
                resolver_context._raise_if_stored()

            if context._exc._has_raised():
                if c_result is not NULL:
                    tree.xmlFreeDoc(c_result)
                    c_result = NULL
                context._exc._raise_if_stored()

            if c_result is NULL:
                # last error seems to be the most accurate here
                error = self._error_log.last_error
                if error is not None and error.message:
                    if error.line > 0:
                        message = u"%s, line %d" % (error.message, error.line)
                    else:
                        message = error.message
                elif error is not None and error.line > 0:
                    message = u"Error applying stylesheet, line %d" % error.line
                else:
                    message = u"Error applying stylesheet"
                raise XSLTApplyError(message, self._error_log)
        finally:
            if resolver_context is not None:
                resolver_context.clear()

        result_doc = _documentFactory(c_result, input_doc._parser)

        c_dict = c_result.dict
        __GLOBAL_PARSER_CONTEXT.initThreadDictRef(&c_result.dict)
        if c_dict is not c_result.dict or \
                self._c_style.doc.dict is not c_result.dict or \
                input_doc._c_doc.dict is not c_result.dict:
            with nogil:
                if c_dict is not c_result.dict:
                    fixThreadDictNames(<xmlNode*>c_result,
                                       c_dict, c_result.dict)
                if self._c_style.doc.dict is not c_result.dict:
                    fixThreadDictNames(<xmlNode*>c_result,
                                       self._c_style.doc.dict, c_result.dict)
                if input_doc._c_doc.dict is not c_result.dict:
                    fixThreadDictNames(<xmlNode*>c_result,
                                       input_doc._c_doc.dict, c_result.dict)

        return _xsltResultTreeFactory(result_doc, self, profile_doc)

    cdef xmlDoc* _run_transform(self, xmlDoc* c_input_doc,
                                parameters, _XSLTContext context,
                                xslt.xsltTransformContext* transform_ctxt):
        cdef xmlDoc* c_result
        cdef char** params
        cdef Py_ssize_t i, parameter_count

        xslt.xsltSetTransformErrorFunc(transform_ctxt, <void*>self._error_log,
                                       _receiveXSLTError)

        if self._access_control is not None:
            self._access_control._register_in_context(transform_ctxt)

        parameter_count = python.PyDict_Size(parameters)
        if parameter_count > 0:
            # allocate space for parameters
            # * 2 as we want an entry for both key and value,
            # and + 1 as array is NULL terminated
            params = <char**>python.PyMem_Malloc(
                sizeof(char*) * (parameter_count * 2 + 1))
            try:
                i = 0
                keep_ref = []
                for key, value in parameters.items():
                    k = _utf8(key)
                    python.PyList_Append(keep_ref, k)
                    v = _utf8(value)
                    python.PyList_Append(keep_ref, v)
                    params[i] = _cstr(k)
                    i += 1
                    params[i] = _cstr(v)
                    i += 1
            except:
                python.PyMem_Free(params)
                raise
            params[i] = NULL
        else:
            params = NULL

        with nogil:
            c_result = xslt.xsltApplyStylesheetUser(
                self._c_style, c_input_doc, params, NULL, NULL, transform_ctxt)

        if params is not NULL:
            # deallocate space for parameters
            python.PyMem_Free(params)

        return c_result

cdef extern from "etree_defs.h":
    # macro call to 't->tp_new()' for instantiation without calling __init__()
    cdef XSLT NEW_XSLT "PY_NEW" (object t)

cdef XSLT _copyXSLT(XSLT stylesheet):
    cdef XSLT new_xslt
    cdef xmlDoc* c_doc
    new_xslt = NEW_XSLT(XSLT) # without calling __init__()
    new_xslt._access_control = stylesheet._access_control
    new_xslt._error_log = _ErrorLog()
    new_xslt._context = stylesheet._context._copy()

    new_xslt._xslt_resolver_context = stylesheet._xslt_resolver_context._copy()
    new_xslt._xslt_resolver_context._c_style_doc = _copyDoc(
        stylesheet._xslt_resolver_context._c_style_doc, 1)

    c_doc = _copyDoc(stylesheet._c_style.doc, 1)
    new_xslt._c_style = xslt.xsltParseStylesheetDoc(c_doc)
    if new_xslt._c_style is NULL:
        tree.xmlFreeDoc(c_doc)
        python.PyErr_NoMemory()

    return new_xslt

cdef class _XSLTResultTree(_ElementTree):
    cdef XSLT _xslt
    cdef _Document _profile
    cdef char* _buffer
    cdef Py_ssize_t _buffer_len
    cdef Py_ssize_t _buffer_refcnt
    cdef _saveToStringAndSize(self, char** s, int* l):
        cdef _Document doc
        cdef int r
        if self._context_node is not None:
            doc = self._context_node._doc
        if doc is None:
            doc = self._doc
            if doc is None:
                s[0] = NULL
                return
        with nogil:
            r = xslt.xsltSaveResultToString(s, l, doc._c_doc,
                                            self._xslt._c_style)
        if r == -1:
            python.PyErr_NoMemory()

    def __str__(self):
        cdef char* s
        cdef int l
        if python.IS_PYTHON3:
            return self.__unicode__()
        self._saveToStringAndSize(&s, &l)
        if s is NULL:
            return ''
        # we must not use 'funicode' here as this is not always UTF-8
        try:
            result = python.PyString_FromStringAndSize(s, l)
        finally:
            tree.xmlFree(s)
        return result

    def __unicode__(self):
        cdef char* encoding
        cdef char* s
        cdef int l
        self._saveToStringAndSize(&s, &l)
        if s is NULL:
            return u''
        encoding = self._xslt._c_style.encoding
        if encoding is NULL:
            encoding = 'ascii'
        try:
            result = python.PyUnicode_Decode(s, l, encoding, 'strict')
        finally:
            tree.xmlFree(s)
        return _stripEncodingDeclaration(result)

    def __getbuffer__(self, Py_buffer* buffer, int flags):
        cdef int l
        if buffer is NULL:
            return # LOCK
        if self._buffer is NULL or flags & python.PyBUF_WRITABLE:
            self._saveToStringAndSize(<char**>&buffer.buf, &l)
            buffer.len = l
            if self._buffer is NULL and not flags & python.PyBUF_WRITABLE:
                self._buffer = <char*>buffer.buf
                self._buffer_len = l
                self._buffer_refcnt = 1
        else:
            buffer.buf = <char*>self._buffer
            buffer.len = self._buffer_len
            self._buffer_refcnt += 1
        if flags & python.PyBUF_WRITABLE:
            buffer.readonly = 0
        else:
            buffer.readonly = 1
        if flags & python.PyBUF_FORMAT:
            buffer.format = "B"
        else:
            buffer.format = NULL
        buffer.ndim = 0
        buffer.shape = NULL
        buffer.strides = NULL
        buffer.suboffsets = NULL
        buffer.itemsize = 1
        buffer.internal = NULL

    def __releasebuffer__(self, Py_buffer* buffer):
        if buffer is NULL:
            return # UNLOCK
        if <char*>buffer.buf is self._buffer:
            self._buffer_refcnt -= 1
            if self._buffer_refcnt == 0:
                tree.xmlFree(self._buffer)
                self._buffer = NULL
        else:
            tree.xmlFree(<char*>buffer.buf)
        buffer.buf = NULL

    property xslt_profile:
        u"""Return an ElementTree with profiling data for the stylesheet run.
        """
        def __get__(self):
            cdef object root
            if self._profile is None:
                return None
            root = self._profile.getroot()
            if root is None:
                return None
            return ElementTree(root)

        def __del__(self):
            self._profile = None

cdef _xsltResultTreeFactory(_Document doc, XSLT xslt, _Document profile):
    cdef _XSLTResultTree result
    result = <_XSLTResultTree>_newElementTree(doc, None, _XSLTResultTree)
    result._xslt = xslt
    result._profile = profile
    result._buffer = NULL
    result._buffer_refcnt = 0
    result._buffer_len = 0
    return result

# functions like "output" and "write" are a potential security risk, but we
# rely on the user to configure XSLTAccessControl as needed
xslt.xsltRegisterAllExtras()

# enable EXSLT support for XSLT
xslt.exsltRegisterAll()

cdef void initTransformDict(xslt.xsltTransformContext* transform_ctxt):
    __GLOBAL_PARSER_CONTEXT.initThreadDictRef(&transform_ctxt.dict)


################################################################################
# XSLT PI support

cdef object _FIND_PI_ATTRIBUTES
_FIND_PI_ATTRIBUTES = re.compile(ur'\s+(\w+)\s*=\s*["\']([^"\']+)["\']', re.U).findall

cdef object _RE_PI_HREF
_RE_PI_HREF = re.compile(ur'\s+href\s*=\s*["\']([^"\']+)["\']')

cdef object _FIND_PI_HREF
_FIND_PI_HREF = _RE_PI_HREF.findall

cdef object _REPLACE_PI_HREF
_REPLACE_PI_HREF = _RE_PI_HREF.sub

cdef XPath __findStylesheetByID
__findStylesheetByID = None

cdef _findStylesheetByID(_Document doc, id):
    global __findStylesheetByID
    if __findStylesheetByID is None:
        __findStylesheetByID = XPath(
            u"//xsl:stylesheet[@xml:id = $id]",
            namespaces={u"xsl" : u"http://www.w3.org/1999/XSL/Transform"})
    return __findStylesheetByID(doc, id=id)

cdef class _XSLTProcessingInstruction(PIBase):
    def parseXSL(self, parser=None):
        u"""Try to parse the stylesheet referenced by this PI and return an
        ElementTree for it.  If the stylesheet is embedded in the same
        document (referenced via xml:id), find and return an ElementTree for
        the stylesheet Element.

        The optional ``parser`` keyword argument can be passed to specify the
        parser used to read from external stylesheet URLs.
        """
        cdef _Document result_doc
        cdef _Element  result_node
        cdef char* c_href
        cdef xmlAttr* c_attr
        if self._c_node.content is NULL:
            raise ValueError, u"PI lacks content"
        hrefs_utf = _FIND_PI_HREF(' ' + self._c_node.content)
        if len(hrefs_utf) != 1:
            raise ValueError, u"malformed PI attributes"
        href_utf = hrefs_utf[0]
        c_href = _cstr(href_utf)

        if c_href[0] != c'#':
            # normal URL, try to parse from it
            c_href = tree.xmlBuildURI(
                c_href,
                tree.xmlNodeGetBase(self._c_node.doc, self._c_node))
            if c_href is not NULL:
                href_utf = c_href
                tree.xmlFree(c_href)
            result_doc = _parseDocumentFromURL(href_utf, parser)
            return _elementTreeFactory(result_doc, None)

        # ID reference to embedded stylesheet
        # try XML:ID lookup
        c_href += 1 # skip leading '#'
        c_attr = tree.xmlGetID(self._c_node.doc, c_href)
        if c_attr is not NULL and c_attr.doc is self._c_node.doc:
            result_node = _elementFactory(self._doc, c_attr.parent)
            return _elementTreeFactory(result_node._doc, result_node)

        # try XPath search
        root = _findStylesheetByID(self._doc, funicode(c_href))
        if not root:
            raise ValueError, u"reference to non-existing embedded stylesheet"
        elif len(root) > 1:
            raise ValueError, u"ambiguous reference to embedded stylesheet"
        result_node = root[0]
        return _elementTreeFactory(result_node._doc, result_node)

    def set(self, key, value):
        if key != u"href":
            raise AttributeError, \
                u"only setting the 'href' attribute is supported on XSLT-PIs"
        if value is None:
            attrib = u""
        elif u'"' in value or u'>' in value:
            raise ValueError, u"Invalid URL, must not contain '\"' or '>'"
        else:
            attrib = u' href="%s"' % value
        text = u' ' + self.text
        if _FIND_PI_HREF(text):
            self.text = _REPLACE_PI_HREF(attrib, text)
        else:
            self.text = text + attrib

    def get(self, key, default=None):
        for attr, value in _FIND_PI_ATTRIBUTES(u' ' + self.text):
            if attr == key:
                return value
        return default
