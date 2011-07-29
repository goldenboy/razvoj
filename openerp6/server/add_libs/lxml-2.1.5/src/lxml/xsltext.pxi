# XSLT extension elements

cdef class XSLTExtension:
    u"""Base class of an XSLT extension element.
    """
    def execute(self, context, self_node, input_node, output_parent):
        u"""execute(self, context, self_node, input_node, output_parent)
        Execute this extension element.

        Subclasses must override this method.  They may append
        elements to the `output_parent` element here, or set its text
        content.  To this end, the `input_node` provides read-only
        access to the current node in the input document, and the
        `self_node` points to the extension element in the stylesheet.
        """
        pass

    def apply_templates(self, _XSLTContext context not None, node):
        u"""apply_templates(self, context, node)

        Call this method to retrieve the result of applying templates
        to an element.

        The return value is a list of elements or text strings that
        were generated by the XSLT processor.
        """
        cdef xmlNode* c_parent
        cdef xmlNode* c_node
        cdef xmlNode* c_next
        cdef xmlNode* c_context_node
        cdef _ReadOnlyElementProxy proxy
        c_context_node = _roNodeOf(node)
        #assert c_context_node.doc is context._xsltContext.node.doc, \
        #    "switching input documents during transformation is not currently supported"

        c_parent = tree.xmlNewDocNode(
            context._xsltCtxt.output, NULL, "fake-parent", NULL)

        c_node = context._xsltCtxt.insert
        context._xsltCtxt.insert = c_parent
        xslt.xsltProcessOneNode(
            context._xsltCtxt, c_context_node, NULL)
        context._xsltCtxt.insert = c_node

        results = [] # or maybe _collectAttributes(c_parent, 2) ?
        c_node = c_parent.children
        try:
            while c_node is not NULL:
                c_next = c_node.next
                if c_node.type == tree.XML_TEXT_NODE:
                    python.PyList_Append(
                        results, funicode(c_node.content))
                elif c_node.type == tree.XML_ELEMENT_NODE:
                    proxy = _newReadOnlyProxy(
                        context._extension_element_proxy, c_node)
                    python.PyList_Append(results, proxy)
                    # unlink node and make sure it will be freed later on
                    tree.xmlUnlinkNode(c_node)
                    proxy.free_after_use()
                else:
                    raise TypeError, \
                        u"unsupported XSLT result type: %d" % c_node.type
                c_node = c_next
        finally:
            # free all intermediate nodes that will not be freed by proxies
            tree.xmlFreeNode(c_parent)
        return results


cdef _registerXSLTExtensions(xslt.xsltTransformContext* c_ctxt,
                             extension_dict):
    for ns_utf, name_utf in extension_dict:
        xslt.xsltRegisterExtElement(
            c_ctxt, _cstr(name_utf), _cstr(ns_utf), _callExtensionElement)

cdef void _callExtensionElement(xslt.xsltTransformContext* c_ctxt,
                                xmlNode* c_context_node,
                                xmlNode* c_inst_node,
                                void* dummy) with gil:
    cdef _XSLTContext context
    cdef XSLTExtension extension
    cdef python.PyObject* dict_result
    cdef char* c_uri
    cdef _ReadOnlyElementProxy context_node, self_node, output_parent
    c_uri = _getNs(c_inst_node)
    if c_uri is NULL:
        # not allowed, and should never happen
        return
    if c_ctxt.xpathCtxt.userData is NULL:
        # just for safety, should never happen
        return
    context = <_XSLTContext>c_ctxt.xpathCtxt.userData
    try:
        dict_result = python.PyDict_GetItem(
            context._extension_elements, (c_uri, c_inst_node.name))
        if dict_result is NULL:
            raise KeyError, \
                u"extension element %s not found" % funicode(c_inst_node.name)
        extension = <object>dict_result

        try:
            self_node     = _newReadOnlyProxy(None, c_inst_node)
            context_node  = _newReadOnlyProxy(self_node, c_context_node)
            output_parent = _newAppendOnlyProxy(self_node, c_ctxt.insert)

            context._extension_element_proxy = self_node
            extension.execute(context, self_node, context_node, output_parent)
        finally:
            context._extension_element_proxy = None
            if self_node is not None:
                _freeReadOnlyProxies(self_node)
    except Exception, e:
        e = unicode(e).encode(u"UTF-8")
        message = python.PyString_FromFormat(
            "Error executing extension element '%s': %s",
            c_inst_node.name, _cstr(e))
        xslt.xsltTransformError(c_ctxt, NULL, c_inst_node, message)
        context._exc._store_raised()
    except:
        # just in case
        message = python.PyString_FromFormat(
            "Error executing extension element '%s'", c_inst_node.name)
        xslt.xsltTransformError(c_ctxt, NULL, c_inst_node, message)
        context._exc._store_raised()