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
from openobject import rpc

from openerp.widgets import TinyWidget


class Sidebar(TinyWidget):

    template = "/openerp/widgets/templates/sidebar.mako"
    params = ['reports', 'actions', 'relates', 'attachments', 'sub_menu', 'view_type', 'model', 'id', 'ctx']

    def add_remote_action_values(self, action_type, current_actions):
        actions = rpc.RPCProxy('ir.values').get(
            'action', action_type, [(self.model, False)], False, self.context)
        for action in [a[-1] for a in actions]:
            if action['id'] not in [a['id'] for a in current_actions]:
                action['context'] = self.context
                current_actions.append(action)

    def __init__(self, model, submenu=None, toolbar=None, id=None, view_type="form", multi=True, context=None, **kw):
        super(Sidebar, self).__init__(model=model, id=id)
        self.multi = multi
        self.context = context or {}
        self.ctx = context
        self.view_type = view_type
        toolbar = toolbar or {}
        submenu = submenu
        self.id = id or None 
        self.reports = toolbar.get('print', [])
        self.actions = toolbar.get('action', [])
        self.relates = toolbar.get('relate', [])
        self.attachments = []
        self.sub_menu = None
                    
        action = 'client_action_multi'
        if self.view_type == 'form':
            action = 'tree_but_action'
        self.add_remote_action_values(action, self.actions)

        self.add_remote_action_values('client_print_multi', self.reports)

        if self.view_type == 'form' and id:
            attachments = rpc.RPCProxy('ir.attachment')
            attachment_ids = attachments.search(
                [('res_model', '=', model), ('res_id', '=', id), ('type', 'in', ['binary', 'url'])],
                0, 0, 0, self.context)

            if attachment_ids:
                self.attachments = attachments.read(attachment_ids, ['name', 'url', 'type'])

            self.sub_menu = submenu
