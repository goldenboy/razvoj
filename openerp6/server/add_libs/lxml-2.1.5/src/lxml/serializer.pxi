# XML serialization and output functions

cdef enum _OutputMethods:
    OUTPUT_METHOD_XML
    OUTPUT_METHOD_HTML
    OUTPUT_METHOD_TEXT

cdef int _findOutputMethod(method) except -1:
    if method is None:
        return OUTPUT_METHOD_XML
    method = method.lower()
    if method == u"xml":
        return OUTPUT_METHOD_XML
    if method == u"html":
        return OUTPUT_METHOD_HTML
    if method == u"text":
        return OUTPUT_METHOD_TEXT
    raise ValueError, u"unknown output method %r" % method

cdef _textToString(xmlNode* c_node, encoding, bint with_tail):
    cdef bint needs_conversion
    cdef char* c_text
    cdef xmlNode* c_text_node
    cdef tree.xmlBuffer* c_buffer

    c_buffer = tree.xmlBufferCreate()
    if c_buffer is NULL:
        return python.PyErr_NoMemory()

    with nogil:
        tree.xmlNodeBufGetContent(c_buffer, c_node)
        if with_tail:
            c_text_node = _textNodeOrSkip(c_node.next)
            while c_text_node is not NULL:
                tree.xmlBufferWriteChar(c_buffer, c_text_node.content)
                c_text_node = _textNodeOrSkip(c_text_node.next)
        c_text = tree.xmlBufferContent(c_buffer)

    try:
        needs_conversion = 0
        if encoding is _unicode:
            needs_conversion = 1
        elif encoding is not None:
            encoding = encoding.upper()
            if encoding != u'UTF-8':
                if encoding == u'ASCII':
                    if isutf8(c_text):
                        # will raise a decode error below
                        needs_conversion = 1
                else:
                    needs_conversion = 1

        if needs_conversion:
            text = python.PyUnicode_DecodeUTF8(
                c_text, tree.xmlBufferLength(c_buffer), 'strict')
            if encoding is not _unicode:
                encoding = _utf8(encoding)
                text = python.PyUnicode_AsEncodedString(
                    text, encoding, 'strict')
        else:
            text = c_text
    finally:
        tree.xmlBufferFree(c_buffer);
    return text


cdef _tostring(_Element element, encoding, method,
               bint write_xml_declaration, bint write_complete_document,
               bint pretty_print, bint with_tail):
    u"""Serialize an element to an encoded string representation of its XML
    tree.
    """
    cdef tree.xmlOutputBuffer* c_buffer
    cdef tree.xmlBuffer* c_result_buffer
    cdef tree.xmlCharEncodingHandler* enchandler
    cdef char* c_enc
    cdef char* c_version
    cdef int c_method
    if element is None:
        return None
    c_method = _findOutputMethod(method)
    if c_method == OUTPUT_METHOD_TEXT:
        return _textToString(element._c_node, encoding, with_tail)
    if encoding is None or encoding is _unicode:
        c_enc = NULL
    else:
        encoding = _utf8(encoding)
        c_enc = _cstr(encoding)
    # it is necessary to *and* find the encoding handler *and* use
    # encoding during output
    enchandler = tree.xmlFindCharEncodingHandler(c_enc)
    if enchandler is NULL and c_enc is not NULL:
        if encoding is not None:
            encoding = encoding.decode(u'UTF-8')
        raise LookupError, u"unknown encoding: '%s'" % encoding
    c_buffer = tree.xmlAllocOutputBuffer(enchandler)
    if c_buffer is NULL:
        tree.xmlCharEncCloseFunc(enchandler)
        return python.PyErr_NoMemory()

    with nogil:
        _writeNodeToBuffer(c_buffer, element._c_node, c_enc, c_method,
                           write_xml_declaration, write_complete_document,
                           pretty_print, with_tail)
        tree.xmlOutputBufferFlush(c_buffer)
        if c_buffer.conv is not NULL:
            c_result_buffer = c_buffer.conv
        else:
            c_result_buffer = c_buffer.buffer

    try:
        if encoding is _unicode:
            result = python.PyUnicode_DecodeUTF8(
                tree.xmlBufferContent(c_result_buffer),
                tree.xmlBufferLength(c_result_buffer),
                'strict')
        else:
            result = python.PyString_FromStringAndSize(
                tree.xmlBufferContent(c_result_buffer),
                tree.xmlBufferLength(c_result_buffer))
    finally:
        tree.xmlOutputBufferClose(c_buffer)
    return result

cdef void _writeNodeToBuffer(tree.xmlOutputBuffer* c_buffer,
                             xmlNode* c_node, char* encoding, int c_method,
                             bint write_xml_declaration,
                             bint write_complete_document,
                             bint pretty_print, bint with_tail) nogil:
    cdef xmlDoc* c_doc
    cdef xmlNode* c_nsdecl_node
    c_doc = c_node.doc
    if write_xml_declaration and c_method == OUTPUT_METHOD_XML:
        _writeDeclarationToBuffer(c_buffer, c_doc.version, encoding)

    # write internal DTD subset, preceding PIs/comments, etc.
    if write_complete_document:
        _writeDtdToBuffer(c_buffer, c_doc, c_node.name, encoding)
        _writePrevSiblings(c_buffer, c_node, encoding, pretty_print)

    c_nsdecl_node = c_node
    if c_node.parent is NULL or c_node.parent.type != tree.XML_DOCUMENT_NODE:
        # copy the node and add namespaces from parents
        # this is required to make libxml write them
        c_nsdecl_node = tree.xmlCopyNode(c_node, 2)
        _copyParentNamespaces(c_node, c_nsdecl_node)

        c_nsdecl_node.parent = c_node.parent
        c_nsdecl_node.children = c_node.children
        c_nsdecl_node.last = c_node.last

    # write node
    if c_method == OUTPUT_METHOD_XML:
        tree.xmlNodeDumpOutput(
            c_buffer, c_doc, c_nsdecl_node, 0, pretty_print, encoding)
    else:
        tree.htmlNodeDumpFormatOutput(
            c_buffer, c_doc, c_nsdecl_node, encoding, pretty_print)

    if c_nsdecl_node is not c_node:
        # clean up
        c_nsdecl_node.children = c_nsdecl_node.last = NULL
        tree.xmlFreeNode(c_nsdecl_node)

    # write tail, trailing comments, etc.
    if with_tail:
        _writeTail(c_buffer, c_node, encoding, pretty_print)
    if write_complete_document:
        _writeNextSiblings(c_buffer, c_node, encoding, pretty_print)
    if pretty_print:
        tree.xmlOutputBufferWriteString(c_buffer, "\n")

cdef void _writeDeclarationToBuffer(tree.xmlOutputBuffer* c_buffer,
                                    char* version, char* encoding) nogil:
    if version is NULL:
        version = "1.0"
    tree.xmlOutputBufferWriteString(c_buffer, "<?xml version='")
    tree.xmlOutputBufferWriteString(c_buffer, version)
    tree.xmlOutputBufferWriteString(c_buffer, "' encoding='")
    tree.xmlOutputBufferWriteString(c_buffer, encoding)
    tree.xmlOutputBufferWriteString(c_buffer, "'?>\n")

cdef void _writeDtdToBuffer(tree.xmlOutputBuffer* c_buffer,
                            xmlDoc* c_doc, char* c_root_name,
                            char* encoding) nogil:
    cdef tree.xmlDtd* c_dtd
    cdef xmlNode* c_node
    c_dtd = c_doc.intSubset
    if c_dtd is NULL or c_dtd.name is NULL:
        return
    if cstd.strcmp(c_root_name, c_dtd.name) != 0:
        return
    tree.xmlOutputBufferWrite(c_buffer, 10, "<!DOCTYPE ")
    tree.xmlOutputBufferWriteString(c_buffer, c_dtd.name)
    if c_dtd.SystemID != NULL and c_dtd.SystemID[0] != c'\0':
        if c_dtd.ExternalID != NULL and c_dtd.ExternalID[0] != c'\0':
            tree.xmlOutputBufferWrite(c_buffer, 9, ' PUBLIC "')
            tree.xmlOutputBufferWriteString(c_buffer, c_dtd.ExternalID)
            tree.xmlOutputBufferWrite(c_buffer, 3, '" "')
        else:
            tree.xmlOutputBufferWrite(c_buffer, 9, ' SYSTEM "')
        tree.xmlOutputBufferWriteString(c_buffer, c_dtd.SystemID)
        tree.xmlOutputBufferWrite(c_buffer, 1, '"')
    if c_dtd.entities == NULL and c_dtd.elements == NULL and \
           c_dtd.attributes == NULL and c_dtd.notations == NULL and \
           c_dtd.pentities == NULL:
        tree.xmlOutputBufferWrite(c_buffer, 2, '>\n')
        return
    tree.xmlOutputBufferWrite(c_buffer, 3, ' [\n')
    if c_dtd.notations != NULL:
        tree.xmlDumpNotationTable(c_buffer.buffer,
                                  <tree.xmlNotationTable*>c_dtd.notations)
    c_node = c_dtd.children
    while c_node is not NULL:
        tree.xmlNodeDumpOutput(c_buffer, c_node.doc, c_node, 0, 0, encoding)
        c_node = c_node.next
    tree.xmlOutputBufferWrite(c_buffer, 3, "]>\n")

cdef void _writeTail(tree.xmlOutputBuffer* c_buffer, xmlNode* c_node,
                     char* encoding, bint pretty_print) nogil:
    u"Write the element tail."
    c_node = c_node.next
    while c_node is not NULL and c_node.type == tree.XML_TEXT_NODE:
        tree.xmlNodeDumpOutput(c_buffer, c_node.doc, c_node, 0,
                               pretty_print, encoding)
        c_node = c_node.next

cdef void _writePrevSiblings(tree.xmlOutputBuffer* c_buffer, xmlNode* c_node,
                             char* encoding, bint pretty_print) nogil:
    cdef xmlNode* c_sibling
    if c_node.parent is not NULL and _isElement(c_node.parent):
        return
    # we are at a root node, so add PI and comment siblings
    c_sibling = c_node
    while c_sibling.prev != NULL and \
            (c_sibling.prev.type == tree.XML_PI_NODE or \
                 c_sibling.prev.type == tree.XML_COMMENT_NODE):
        c_sibling = c_sibling.prev
    while c_sibling != c_node:
        tree.xmlNodeDumpOutput(c_buffer, c_node.doc, c_sibling, 0,
                               pretty_print, encoding)
        if pretty_print:
            tree.xmlOutputBufferWriteString(c_buffer, "\n")
        c_sibling = c_sibling.next

cdef void _writeNextSiblings(tree.xmlOutputBuffer* c_buffer, xmlNode* c_node,
                             char* encoding, bint pretty_print) nogil:
    cdef xmlNode* c_sibling
    if c_node.parent is not NULL and _isElement(c_node.parent):
        return
    # we are at a root node, so add PI and comment siblings
    c_sibling = c_node.next
    while c_sibling != NULL and \
            (c_sibling.type == tree.XML_PI_NODE or \
                 c_sibling.type == tree.XML_COMMENT_NODE):
        if pretty_print:
            tree.xmlOutputBufferWriteString(c_buffer, "\n")
        tree.xmlNodeDumpOutput(c_buffer, c_node.doc, c_sibling, 0,
                               pretty_print, encoding)
        c_sibling = c_sibling.next

# output to file-like objects

cdef class _FilelikeWriter:
    cdef object _filelike
    cdef _ExceptionContext _exc_context
    cdef _ErrorLog error_log
    def __init__(self, filelike, exc_context=None):
        self._filelike = filelike
        if exc_context is None:
            self._exc_context = _ExceptionContext()
        else:
            self._exc_context = exc_context
        self.error_log = _ErrorLog()

    cdef tree.xmlOutputBuffer* _createOutputBuffer(
        self, tree.xmlCharEncodingHandler* enchandler) except NULL:
        cdef tree.xmlOutputBuffer* c_buffer
        c_buffer = tree.xmlOutputBufferCreateIO(
            _writeFilelikeWriter, _closeFilelikeWriter,
            <python.PyObject*>self, enchandler)
        if c_buffer is NULL:
            raise IOError, u"Could not create I/O writer context."
        return c_buffer

    cdef int write(self, char* c_buffer, int size):
        try:
            if self._filelike is None:
                raise IOError, u"File is already closed"
            py_buffer = python.PyString_FromStringAndSize(c_buffer, size)
            self._filelike.write(py_buffer)
            return size
        except:
            self._exc_context._store_raised()
            return -1

    cdef int close(self):
        # we should not close the file here as we didn't open it
        self._filelike = None
        return 0

cdef int _writeFilelikeWriter(void* ctxt, char* c_buffer, int len):
    return (<_FilelikeWriter>ctxt).write(c_buffer, len)

cdef int _closeFilelikeWriter(void* ctxt):
    return (<_FilelikeWriter>ctxt).close()

cdef _tofilelike(f, _Element element, encoding, method,
                 bint write_xml_declaration, bint write_doctype,
                 bint pretty_print, bint with_tail):
    cdef python.PyThreadState* state
    cdef _FilelikeWriter writer
    cdef tree.xmlOutputBuffer* c_buffer
    cdef tree.xmlCharEncodingHandler* enchandler
    cdef char* c_enc
    if encoding is None:
        c_enc = NULL
    else:
        encoding = _utf8(encoding)
        c_enc = _cstr(encoding)
    c_method = _findOutputMethod(method)
    if c_method == OUTPUT_METHOD_TEXT:
        if _isString(f):
            filename8 = _encodeFilename(f)
            f = open(filename8, u'wb')
            try:
                f.write(_textToString(element._c_node, encoding, with_tail))
            finally:
                f.close()
        else:
            f.write(_textToString(element._c_node, encoding, with_tail))
        return
    enchandler = tree.xmlFindCharEncodingHandler(c_enc)
    if enchandler is NULL:
        if encoding is not None:
            encoding = encoding.decode(u'UTF-8')
        raise LookupError, u"unknown encoding: '%s'" % encoding

    if _isString(f):
        filename8 = _encodeFilename(f)
        c_buffer = tree.xmlOutputBufferCreateFilename(
            _cstr(filename8), enchandler, 0)
        if c_buffer is NULL:
            return python.PyErr_SetFromErrno(IOError)
        state = python.PyEval_SaveThread()
    elif hasattr(f, u'write'):
        writer   = _FilelikeWriter(f)
        c_buffer = writer._createOutputBuffer(enchandler)
    else:
        tree.xmlCharEncCloseFunc(enchandler)
        raise TypeError, \
            u"File or filename expected, got '%s'" % funicode(python._fqtypename(f))

    _writeNodeToBuffer(c_buffer, element._c_node, c_enc, c_method,
                       write_xml_declaration, write_doctype,
                       pretty_print, with_tail)
    tree.xmlOutputBufferClose(c_buffer)
    if writer is None:
        python.PyEval_RestoreThread(state)
    else:
        writer._exc_context._raise_if_stored()

cdef _tofilelikeC14N(f, _Element element):
    cdef _FilelikeWriter writer
    cdef tree.xmlOutputBuffer* c_buffer
    cdef char* c_filename
    cdef xmlDoc* c_base_doc
    cdef xmlDoc* c_doc
    cdef int bytes

    c_base_doc = element._c_node.doc
    c_doc = _fakeRootDoc(c_base_doc, element._c_node)
    try:
        if _isString(f):
            filename8 = _encodeFilename(f)
            c_filename = _cstr(filename8)
            with nogil:
                bytes = c14n.xmlC14NDocSave(c_doc, NULL, 0, NULL, 1,
                                            c_filename, 0)
        elif hasattr(f, u'write'):
            writer   = _FilelikeWriter(f)
            c_buffer = writer._createOutputBuffer(NULL)
            writer.error_log.connect()
            bytes = c14n.xmlC14NDocSaveTo(c_doc, NULL, 0, NULL, 1, c_buffer)
            writer.error_log.disconnect()
            tree.xmlOutputBufferClose(c_buffer)
        else:
            raise TypeError, \
                u"File or filename expected, got '%s'" % funicode(python._fqtypename(f))
    finally:
        _destroyFakeDoc(c_base_doc, c_doc)

    if writer is not None:
        writer._exc_context._raise_if_stored()

    if bytes < 0:
        message = u"C14N failed"
        if writer is not None:
            errors = writer.error_log
            if len(errors):
                message = errors[0].message
        raise C14NError, message

# dump node to file (mainly for debug)

cdef _dumpToFile(f, xmlNode* c_node, bint pretty_print, bint with_tail):
    cdef tree.xmlOutputBuffer* c_buffer
    cdef cstd.FILE* c_file
    c_file = python.PyFile_AsFile(f)
    if c_file is NULL:
        raise ValueError, u"not a file"
    c_buffer = tree.xmlOutputBufferCreateFile(c_file, NULL)
    tree.xmlNodeDumpOutput(c_buffer, c_node.doc, c_node, 0, pretty_print, NULL)
    if with_tail:
        _writeTail(c_buffer, c_node, NULL, 0)
    if not pretty_print:
        # not written yet
        tree.xmlOutputBufferWriteString(c_buffer, '\n')
    tree.xmlOutputBufferFlush(c_buffer)
