###############################################################################
#
#  Copyright (C) 2007-TODAY OpenERP SA. All Rights Reserved.
#
#  $Id$
#
#  Developed by OpenERP (http://openerp.com) and Axelor (http://axelor.com).
#
#  The OpenERP web client is distributed under the "OpenERP Public License".
#  It's based on Mozilla Public License Version (MPL) 1.1 with following 
#  restrictions:
#
#  -   All names, links and logos of OpenERP must be kept as in original
#      distribution without any changes in all software screens, especially
#      in start-up page and the software header, even if the application
#      source code has been changed or updated or code has been added.
#
#  You can see the MPL licence at: http://www.mozilla.org/MPL/MPL-1.1.html
#
###############################################################################

import xml.dom.minidom

from openobject import rpc
from openobject.tools import url
from openobject.widgets import Form

from openerp.utils import node_attributes

from sidebar import Sidebar
import treegrid


class ViewTree(Form):

    template = "/openerp/widgets/templates/viewtree.mako"
    params = ['model', 'id', 'ids', 'domain', 'context', 'view_id', 'toolbar']
    member_widgets = ['tree', 'sidebar']

    def __init__(self, view, model, res_id=False, domain=[], context={}, action=None, fields=None):
        super(ViewTree, self).__init__(name='view_tree', action=action)

        self.model = view['model']
        self.domain2 = domain or []
        self.context = context or {}
        self.domain = []
        
        fields_info = dict(fields)

        self.field_parent = view.get("field_parent") or None

        if self.field_parent:
            self.domain = domain

        self.view = view
        self.view_id = view['view_id']

        proxy = rpc.RPCProxy(self.model)

        ctx = dict(self.context,
                   **rpc.get_session().context)
                
        dom = xml.dom.minidom.parseString(view['arch'].encode('utf-8'))

        root = dom.childNodes[0]
        attrs = node_attributes(root)
        self.string = attrs.get('string', 'Unknown')
        self.toolbar = attrs.get('toolbar', False)

        ids = []
        id = res_id

        if self.toolbar:
            ids = proxy.search(self.domain2, 0, 0, 0, ctx)
            self.toolbar = proxy.read(ids, ['name', 'icon'], ctx)

            if not id and ids:
                id = ids[0]

            if id:
                ids = proxy.read([id], [self.field_parent])[0][self.field_parent]
        elif not ids:
            ids = proxy.search(domain, 0, 0, 0, ctx)

        self.headers = []
        self.parse(root, fields)

        self.tree = treegrid.TreeGrid(name="tree_%d" % (id),
                                      model=self.model,
                                      headers=self.headers,
                                      url=url("/openerp/tree/data"),
                                      ids=ids,
                                      domain=self.domain,
                                      context=self.context,
                                      field_parent=self.field_parent,
                                      onselection="onSelection",
                                      fields_info=fields_info)
        self.id = id
        self.ids = ids
        self.view_type = view.get('type')

        toolbar = {}
        for item, value in view.get('toolbar', {}).items():
            if value: 
                toolbar[item] = value

        if toolbar:
            self.sidebar = Sidebar(self.model, None, toolbar, self.id, self.view_type, context=self.context)
        else:
            if attrs.get('toolbar') and attrs['toolbar']:
                self.sidebar = Sidebar(self.model, None, None, self.id, self.view_type, context=self.context)
        
        # get the correct view title
        self.string = self.context.get('_terp_view_name', self.string) or self.string

    def parse(self, root, fields=None):

        for node in root.childNodes:

            if not node.nodeType==node.ELEMENT_NODE:
                continue

            attrs = node_attributes(node)

            field = fields.get(attrs['name'])
            if field and not attrs.get('invisible'):
                field.update(attrs)
                self.headers.append(field)

# vim: ts=4 sts=4 sw=4 si et
