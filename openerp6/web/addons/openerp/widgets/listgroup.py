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
import random
from operator import itemgetter

import cherrypy

from openobject import rpc
from openobject.i18n import format

from listgrid import List, CELLTYPES
from pager import Pager


def parse(group_by, hiddens, headers, group_level, groups):
    if isinstance(group_by, list):
        i = 0
        while i < len(group_by):
            if group_by[i] == False:
                del group_by[i]
            else:
                i += 1

    if isinstance(groups, basestring):
        groups = groups.split(',')
    if isinstance(group_by, basestring):
        group_by = group_by.split(',')

    for grp in range(len(group_by)):
        if 'group_' in group_by[grp]:
            if group_by[grp].count('group_') > 1:
                group_by[grp] = 'group_' + group_by[grp].split("group_")[-1]
            else:
                group_by[grp] = group_by[grp].split("group_")[-1]

    for grp_by in groups:
        for hidden in hiddens:
            if grp_by in hidden:
                headers.insert(groups.index(grp_by), hidden)

    for grp_by in groups:
        for cnt, header in enumerate(headers):
            if header[0] == grp_by:
                headers.pop(cnt)
                headers.insert(groups.index(grp_by), header)

    return group_by, hiddens, headers

def parse_groups(group_by, grp_records, headers, ids, model,  offset, limit, context, data, total_fields, fields):
    proxy = rpc.RPCProxy(model)
    grouped = []
    grp_ids = []
    for grp in grp_records:
        inner = {}
        for key, head in headers:
            if not isinstance(head, int):
                kind = head.get('type')
                if kind == 'progressbar':
                    inner[key] = CELLTYPES[kind](value=grp.get(key), **head)
        grouped.append(inner)

    child = len(group_by) == 1
    digits = (16,2)
    if fields:
        for key, val in fields.items():
            if val.get('digits'):
                digits = val['digits']
    if isinstance(digits, basestring):
            digits = eval(digits)
    integer, digit = digits

    if grp_records and total_fields and group_by:
        for sum_key, sum_val in total_fields.items():
            if grp_records[0].has_key(sum_key):
                value = sum(map(lambda x: x[sum_key], grp_records))
                if isinstance(value, float):
                    total_fields[sum_key][1] = format.format_decimal(value or 0.0, digit)
                else:
                    total_fields[sum_key][1] = value
    if grp_records:
        for rec in grp_records:
            for key, val in rec.items():
                if isinstance(val, float):
                    rec[key] = format.format_decimal(val or 0.0, digit)

            for grp_by in group_by:
                if not rec.get(grp_by):
                    rec[grp_by] = ''

            ch_ids = []
            if child:
                rec_dom =  rec.get('__domain')
                dom = [('id', 'in', ids), rec_dom[0]]
                ch_ids = [d for id in proxy.search(dom, offset, 0, 0, context)
                            for  d in data
                            if int(str(d.get('id'))) == id] # Need to convert in String and then Int.
            rec['child_rec'] = ch_ids
            rec['groups_id'] = 'group_' + str(random.randrange(1, 10000))
            if group_by:
                rec['group_by_id'] = group_by[0]+'_'+str(grp_records.index(rec))

    return grouped, grp_ids


class ListGroup(List):

    template = "/openerp/widgets/templates/listgrid/listgroup.mako"
    params = ['grp_records', 'group_by_ctx', 'grouped', 'group_by_no_leaf']

    def __init__(self, name, model, view, ids=[], domain=[], context={}, **kw):

        self.context = context or {}
        self.domain = domain or []
        self.group_by_no_leaf = self.context.get('group_by_no_leaf', 0)
        self.selectable = kw.get('selectable', 0)
        self.editable = kw.get('editable', False)
        self.pageable = kw.get('pageable', True)

        self.offset = kw.get('offset', 0)
        self.limit = kw.get('limit', 0)
        self.count = kw.get('count', 0)
        self.link = kw.get('nolinks')

        proxy = rpc.RPCProxy(model)

        # adding the piece of code to set limit as 0 to get rid of pager's negative offset error.
        # Here, we don't change the self.limit as Pager needs -1 to treat Unlimited limit  atribute
        terp_offset, terp_limit = self.offset, self.limit
        if self.limit < 0:
            terp_offset, terp_limit = 0, 0

        custom_search_domain = getattr(cherrypy.request, 'custom_search_domain', [])
        custom_filter_domain = getattr(cherrypy.request, 'custom_filter_domain', [])

        if custom_search_domain:
            self.domain.extend(i for i in custom_search_domain if i not in domain)

        elif custom_filter_domain:
            self.domain.extend(i for i in custom_filter_domain if i not in domain)


        if ids is None and not self.group_by_no_leaf:

            ids = proxy.search(self.domain, terp_offset, terp_limit, 0, self.context)

            if len(ids) < self.limit:
                self.count = len(ids)
            else:
                self.count = proxy.search_count(domain, context)

        if ids and not isinstance(ids, list):
            ids = [ids]

        self.ids = ids

        self.concurrency_info = None

        self.group_by_ctx = kw.get('group_by_ctx', [])

        if not isinstance(self.group_by_ctx, list):
            self.group_by_ctx = [self.group_by_ctx]

        fields = view['fields']
        self.grp_records = []

        self.context.update(rpc.get_session().context.copy())

        super(ListGroup, self).__init__(
            name=name, model=model, view=view, ids=self.ids, domain=self.domain,
            context=self.context, limit=-1, count=self.count,
            offset=self.offset, editable=self.editable,
            selectable=self.selectable)

        if self.group_by_ctx:
            self.context['group_by'] = self.group_by_ctx
        else:
            self.group_by_ctx = self.context.get('group_by', [])

        self.group_by_ctx, self.hiddens, self.headers = parse(self.group_by_ctx, self.hiddens, self.headers, None, self.group_by_ctx)

        self.grp_records = proxy.read_group(self.context.get('__domain', []) + (self.domain or []),
                                                fields.keys(), self.group_by_ctx, 0, False, self.context)

        terp_params = getattr(cherrypy.request, 'terp_params', [])
        if terp_params.sort_key and terp_params.sort_key in self.group_by_ctx and self.group_by_ctx.index(terp_params.sort_key) == 0:
            if terp_params.sort_order == 'desc':
                rev = True
            else:
                rev = False
            self.grp_records = sorted(self.grp_records, key=itemgetter(terp_params.sort_key), reverse=rev)

        for grp_rec in self.grp_records:
            if not grp_rec.get('__domain'):
                grp_rec['__domain'] = self.context.get('__domain', []) + (self.domain or [])
            if not grp_rec.get('__context'):
                grp_rec['__context'] = {'group_by': self.group_by_ctx}

        self.grouped, grp_ids = parse_groups(self.group_by_ctx, self.grp_records, self.headers, self.ids, model, terp_offset, terp_limit, self.context, self.data, self.field_total, fields)

        if self.pageable:
            self.count = len(self.grouped)
            self.pager = Pager(ids=self.ids, offset=self.offset, limit=self.limit, count=self.count)
            self.pager._name = self.name


class MultipleGroup(List):

    template = "/openerp/widgets/templates/listgrid/multiple_group.mako"
    params = ['grp_records', 'group_by_ctx', 'grouped', 'parent_group', 'group_level', 'group_by_no_leaf']

    def __init__(self, name, model, view, ids=[], domain=[], parent_group=None, group_level=0, groups = [], context={}, **kw):
        self.context = context or {}
        self.domain = domain or []

        self.selectable = kw.get('selectable', 0)
        self.editable = kw.get('editable', False)
        self.pageable = kw.get('pageable', True)

        self.offset = kw.get('offset', 0)
        self.limit = kw.get('limit', 50)
        self.count = kw.get('count', 0)

        self.link = kw.get('nolinks')
        self.parent_group = parent_group or None
        self.group_level = group_level or 0
        sort_key = kw.get('sort_key')
        sort_order = kw.get('sort_order')
        proxy = rpc.RPCProxy(model)
        if ids is None:
            if self.limit > 0:
                ids = proxy.search(self.domain, self.offset, self.limit, 0, rpc.get_session().context.copy())
            else:
                ids = proxy.search(self.domain, 0, 0, 0, rpc.get_session().context.copy())

            if len(ids) < self.limit:
                self.count = len(ids)
            else:
                self.count = proxy.search_count(domain, rpc.get_session().context.copy())

        if ids and not isinstance(ids, list):
            ids = [ids]

        self.ids = ids

        self.concurrency_info = None

        self.group_by_ctx = kw.get('group_by_ctx', [])

        if not isinstance(self.group_by_ctx, list):
            self.group_by_ctx = [self.group_by_ctx]

        fields = view['fields']

        self.grp_records = []
        super(MultipleGroup, self).__init__(
            name=name, model=model, view=view, ids=self.ids, domain=self.domain,
            parent_group=parent_group, group_level=group_level, groups=groups, context=self.context, limit=self.limit,
            count=self.count,offset=self.offset, editable=self.editable,
            selectable=self.selectable)

        self.group_by_no_leaf = self.context.get('group_by_no_leaf', 0)

        self.group_by_ctx, self.hiddens, self.headers = parse(self.group_by_ctx, self.hiddens, self.headers, self.group_level, groups)

        self.grp_records = proxy.read_group(self.context.get('__domain', []),
                                                fields.keys(), self.group_by_ctx, 0, False, self.context)

        if sort_key and sort_key in self.group_by_ctx and self.group_by_ctx.index(sort_key) == 0:
            if sort_order == 'desc':
                rev = True
            else:
                rev = False
            self.grp_records = sorted(self.grp_records, key=itemgetter(sort_key), reverse=rev)
        self.grouped, grp_ids = parse_groups(self.group_by_ctx, self.grp_records, self.headers, self.ids, model,  self.offset, self.limit, rpc.get_session().context.copy(), self.data, self.field_total, fields)
