#ifndef __PYX_HAVE__lxml__etree
#define __PYX_HAVE__lxml__etree
#ifdef __cplusplus
#define __PYX_EXTERN_C extern "C"
#else
#define __PYX_EXTERN_C extern
#endif

typedef xmlNode *(*_node_to_node_function)(xmlNode *);

/* "src/lxml/lxml.etree.pyx":280
 * 
 * 
 * cdef public class _Document [ type LxmlDocumentType, object LxmlDocument ]:             # <<<<<<<<<<<<<<
 *     u"""Internal base class to reference a libxml document.
 * 
 */

struct LxmlDocument {
  PyObject_HEAD
  struct __pyx_vtabstruct_4lxml_5etree__Document *__pyx_vtab;
  int _ns_counter;
  PyObject *_prefix_tail;
  xmlDoc *_c_doc;
  struct __pyx_obj_4lxml_5etree__BaseParser *_parser;
};

/* "src/lxml/lxml.etree.pyx":520
 * 
 * 
 * cdef public class _Element [ type LxmlElementType, object LxmlElement ]:             # <<<<<<<<<<<<<<
 *     u"""Element class.
 * 
 */

struct LxmlElement {
  PyObject_HEAD
  PyObject *_gc_doc;
  struct LxmlDocument *_doc;
  xmlNode *_c_node;
  PyObject *_tag;
  PyObject *_attrib;
};

/* "src/lxml/lxml.etree.pyx":1494
 * 
 * 
 * cdef public class _ElementTree [ type LxmlElementTreeType,             # <<<<<<<<<<<<<<
 *                                  object LxmlElementTree ]:
 *     cdef _Document _doc
 */

struct LxmlElementTree {
  PyObject_HEAD
  struct __pyx_vtabstruct_4lxml_5etree__ElementTree *__pyx_vtab;
  struct LxmlDocument *_doc;
  struct LxmlElement *_context_node;
};

/* "src/lxml/lxml.etree.pyx":2012
 * 
 * 
 * cdef public class _ElementTagMatcher [ object LxmlElementTagMatcher,             # <<<<<<<<<<<<<<
 *                                        type LxmlElementTagMatcherType ]:
 *     cdef object _pystrings
 */

struct LxmlElementTagMatcher {
  PyObject_HEAD
  struct __pyx_vtabstruct_4lxml_5etree__ElementTagMatcher *__pyx_vtab;
  PyObject *_pystrings;
  int _node_type;
  char *_href;
  char *_name;
};

/* "src/lxml/lxml.etree.pyx":2040
 *                 self._name = NULL
 * 
 * cdef public class _ElementIterator(_ElementTagMatcher) [             # <<<<<<<<<<<<<<
 *     object LxmlElementIterator, type LxmlElementIteratorType ]:
 *     # we keep Python references here to control GC
 */

struct LxmlElementIterator {
  struct LxmlElementTagMatcher __pyx_base;
  struct LxmlElement *_node;
  _node_to_node_function _next_element;
};

/* "/home/goran/razvoj/openerp/from_lp/trunk6/client/bin/build/lxml/src/lxml/classlookup.pxi":6
 * # Custom Element classes
 * 
 * cdef public class ElementBase(_Element) [ type LxmlElementBaseType,             # <<<<<<<<<<<<<<
 *                                           object LxmlElementBase ]:
 *     u"""All custom Element classes must inherit from this one.
 */

struct LxmlElementBase {
  struct LxmlElement __pyx_base;
};

typedef PyObject *(*_element_class_lookup_function)(PyObject *, struct LxmlDocument *, xmlNode *);

/* "/home/goran/razvoj/openerp/from_lp/trunk6/client/bin/build/lxml/src/lxml/classlookup.pxi":70
 * 
 * # class to store element class lookup functions
 * cdef public class ElementClassLookup [ type LxmlElementClassLookupType,             # <<<<<<<<<<<<<<
 *                                        object LxmlElementClassLookup ]:
 *     u"""ElementClassLookup(self)
 */

struct LxmlElementClassLookup {
  PyObject_HEAD
  _element_class_lookup_function _lookup_function;
};

/* "/home/goran/razvoj/openerp/from_lp/trunk6/client/bin/build/lxml/src/lxml/classlookup.pxi":79
 *         self._lookup_function = NULL # use default lookup
 * 
 * cdef public class FallbackElementClassLookup(ElementClassLookup) \             # <<<<<<<<<<<<<<
 *          [ type LxmlFallbackElementClassLookupType,
 *            object LxmlFallbackElementClassLookup ]:
 */

struct LxmlFallbackElementClassLookup {
  struct LxmlElementClassLookup __pyx_base;
  struct __pyx_vtabstruct_4lxml_5etree_FallbackElementClassLookup *__pyx_vtab;
  struct LxmlElementClassLookup *fallback;
  _element_class_lookup_function _fallback_function;
};

#ifndef __PYX_HAVE_API__lxml__etree

__PYX_EXTERN_C DL_IMPORT(struct LxmlElement) *deepcopyNodeToDocument(struct LxmlDocument *, xmlNode *);
__PYX_EXTERN_C DL_IMPORT(struct LxmlElementTree) *elementTreeFactory(struct LxmlElement *);
__PYX_EXTERN_C DL_IMPORT(struct LxmlElementTree) *newElementTree(struct LxmlElement *, PyObject *);
__PYX_EXTERN_C DL_IMPORT(struct LxmlElement) *elementFactory(struct LxmlDocument *, xmlNode *);
__PYX_EXTERN_C DL_IMPORT(struct LxmlElement) *makeElement(PyObject *, struct LxmlDocument *, PyObject *, PyObject *, PyObject *, PyObject *, PyObject *);
__PYX_EXTERN_C DL_IMPORT(struct LxmlElement) *makeSubElement(struct LxmlElement *, PyObject *, PyObject *, PyObject *, PyObject *, PyObject *);
__PYX_EXTERN_C DL_IMPORT(void) setElementClassLookupFunction(_element_class_lookup_function, PyObject *);
__PYX_EXTERN_C DL_IMPORT(PyObject) *lookupDefaultElementClass(PyObject *, PyObject *, xmlNode *);
__PYX_EXTERN_C DL_IMPORT(PyObject) *lookupNamespaceElementClass(PyObject *, PyObject *, xmlNode *);
__PYX_EXTERN_C DL_IMPORT(PyObject) *callLookupFallback(struct LxmlFallbackElementClassLookup *, struct LxmlDocument *, xmlNode *);
__PYX_EXTERN_C DL_IMPORT(int) tagMatches(xmlNode *, char *, char *);
__PYX_EXTERN_C DL_IMPORT(struct LxmlDocument) *documentOrRaise(PyObject *);
__PYX_EXTERN_C DL_IMPORT(struct LxmlElement) *rootNodeOrRaise(PyObject *);
__PYX_EXTERN_C DL_IMPORT(int) hasText(xmlNode *);
__PYX_EXTERN_C DL_IMPORT(int) hasTail(xmlNode *);
__PYX_EXTERN_C DL_IMPORT(PyObject) *textOf(xmlNode *);
__PYX_EXTERN_C DL_IMPORT(PyObject) *tailOf(xmlNode *);
__PYX_EXTERN_C DL_IMPORT(int) setNodeText(xmlNode *, PyObject *);
__PYX_EXTERN_C DL_IMPORT(int) setTailText(xmlNode *, PyObject *);
__PYX_EXTERN_C DL_IMPORT(PyObject) *attributeValue(xmlNode *, xmlAttr *);
__PYX_EXTERN_C DL_IMPORT(PyObject) *attributeValueFromNsName(xmlNode *, char *, char *);
__PYX_EXTERN_C DL_IMPORT(PyObject) *getAttributeValue(struct LxmlElement *, PyObject *, PyObject *);
__PYX_EXTERN_C DL_IMPORT(PyObject) *iterattributes(struct LxmlElement *, int);
__PYX_EXTERN_C DL_IMPORT(PyObject) *collectAttributes(xmlNode *, int);
__PYX_EXTERN_C DL_IMPORT(int) setAttributeValue(struct LxmlElement *, PyObject *, PyObject *);
__PYX_EXTERN_C DL_IMPORT(int) delAttribute(struct LxmlElement *, PyObject *);
__PYX_EXTERN_C DL_IMPORT(int) delAttributeFromNsName(xmlNode *, char *, char *);
__PYX_EXTERN_C DL_IMPORT(int) hasChild(xmlNode *);
__PYX_EXTERN_C DL_IMPORT(xmlNode) *findChild(xmlNode *, Py_ssize_t);
__PYX_EXTERN_C DL_IMPORT(xmlNode) *findChildForwards(xmlNode *, Py_ssize_t);
__PYX_EXTERN_C DL_IMPORT(xmlNode) *findChildBackwards(xmlNode *, Py_ssize_t);
__PYX_EXTERN_C DL_IMPORT(xmlNode) *nextElement(xmlNode *);
__PYX_EXTERN_C DL_IMPORT(xmlNode) *previousElement(xmlNode *);
__PYX_EXTERN_C DL_IMPORT(void) appendChild(struct LxmlElement *, struct LxmlElement *);
__PYX_EXTERN_C DL_IMPORT(PyObject) *pyunicode(char *);
__PYX_EXTERN_C DL_IMPORT(PyObject) *utf8(PyObject *);
__PYX_EXTERN_C DL_IMPORT(PyObject) *getNsTag(PyObject *);
__PYX_EXTERN_C DL_IMPORT(PyObject) *namespacedName(xmlNode *);
__PYX_EXTERN_C DL_IMPORT(PyObject) *namespacedNameFromNsName(char *, char *);
__PYX_EXTERN_C DL_IMPORT(void) iteratorStoreNext(struct LxmlElementIterator *, struct LxmlElement *);
__PYX_EXTERN_C DL_IMPORT(void) initTagMatch(struct LxmlElementTagMatcher *, PyObject *);
__PYX_EXTERN_C DL_IMPORT(xmlNs) *findOrBuildNodeNsPrefix(struct LxmlDocument *, xmlNode *, char *, char *);

__PYX_EXTERN_C DL_IMPORT(PyTypeObject) LxmlDocumentType;
__PYX_EXTERN_C DL_IMPORT(PyTypeObject) LxmlElementType;
__PYX_EXTERN_C DL_IMPORT(PyTypeObject) LxmlElementTreeType;
__PYX_EXTERN_C DL_IMPORT(PyTypeObject) LxmlElementTagMatcherType;
__PYX_EXTERN_C DL_IMPORT(PyTypeObject) LxmlElementIteratorType;
__PYX_EXTERN_C DL_IMPORT(PyTypeObject) LxmlElementBaseType;
__PYX_EXTERN_C DL_IMPORT(PyTypeObject) LxmlElementClassLookupType;
__PYX_EXTERN_C DL_IMPORT(PyTypeObject) LxmlFallbackElementClassLookupType;

#endif

PyMODINIT_FUNC initetree(void);

#endif
