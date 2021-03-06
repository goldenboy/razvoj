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
import cherrypy

from openobject import rpc
from openobject.tools import expose

from openerp import widgets as tw, validators
from openerp.utils import common, TinyDict
from openerp.controllers.form import Form


class State(Form):

    _cp_path = "/view_diagram/workflow/state"

    @expose(template="/view_diagram/controllers/templates/wkf_popup.mako")
    def create(self, params, tg_errors=None):

        params.path = self.path
        params.function = 'create_state'

        if params.id and cherrypy.request.path_info == self.path + '/view':
            params.load_counter = 2
        elif not params.context:
            params.context = {'o2m_model': params.o2m_model, 'o2m_id': params.o2m_id}

        proxy_field = rpc.RPCProxy('ir.model.fields')
        field_ids = proxy_field.search([('model', '=', params.o2m_model or params.context.get('o2m_model')), ('relation', '=', params.model)], 0, 0, 0, rpc.get_session().context)
        m2o_field = proxy_field.read(field_ids, ['relation_field'], rpc.get_session().context)[0]['relation_field']

        params.hidden_fields = [
            tw.form.Hidden(name=m2o_field, default=params.o2m_id or params.context.get('o2m_id', False)),
            tw.form.Hidden(name='_terp_o2m_model', default=params.o2m_model)]
        form = self.create_form(params, tg_errors)

        field = form.screen.widget.get_widgets_by_name(m2o_field)
        if field:
            field[0].set_value(params.o2m_id or params.context.get('o2m_id', False))
            field[0].readonly = True

        vals = getattr(cherrypy.request, 'terp_validators', {})
        vals[m2o_field] = validators.Int()

        hide = []

        for w in hide:
            w.visible = False

        return dict(form=form, params=params)

    @expose()
    def edit(self, **kw):
        params, data = TinyDict.split(kw)

        if not params.model:
            params.update(kw)

        params.view_mode = ['form']
        params.view_type = 'form'
        params.editable = True

        return self.create(params)

    @expose('json', methods=('POST',))
    def delete(self, node_obj, id, **kw):

        error_msg = None
        proxy = rpc.RPCProxy(node_obj)
        res_act = proxy.unlink(int(id))

        if not res_act:
            error_msg = _('Could not delete state')

        return dict(error=error_msg)

    @expose('json')
    def get_info(self, node_obj, id, in_transition_field, out_transition_field, **kw):
        node_flds_visible = eval(kw.get('node_flds_v', '[]'))
        node_flds_hidden = eval(kw.get('node_flds_h', '[]'))
        node_flds_string = eval(kw.get('node_flds_string', '[]'))

        bgcolors = {}
        for color_spec in kw.get('bgcolors', '').split(';'):
            if color_spec:
                colour, test = color_spec.split(':')
                bgcolors[colour] = test

        shapes = {}
        for shape_spec in kw.get('shapes', '').split(';'):
            if shape_spec:
                colour, test = shape_spec.split(':')
                shapes[colour] = test

        proxy_act = rpc.RPCProxy(node_obj)
        search_act = proxy_act.search([('id', '=', int(id))], 0, 0, 0, rpc.get_session().context)
        result = proxy_act.read(search_act, [in_transition_field, out_transition_field] + node_flds_visible + node_flds_hidden, rpc.get_session().context)[0]

        data = {
            'id': result['id'],
            'name': result.get('name', ''),
            'color': 'white',
            'shape': 'ellipse',
            in_transition_field: result[in_transition_field],
            out_transition_field: result[out_transition_field],
            'options': {}
        }

        for color, expr in bgcolors.items():
            if eval(expr, result):
                data['color'] = color

        for shape, expr in shapes.items():
            if eval(expr, result):
                data['shape'] = shape

        for i, fld in enumerate(node_flds_visible):
            data['options'][node_flds_string[i]] = result[fld]

        return dict(data=data)


class Connector(Form):

    _cp_path = "/view_diagram/workflow/connector"

    @expose(template="/view_diagram/controllers/templates/wkf_popup.mako")
    def create(self, params, tg_errors=None):

        params.path = self.path
        params.function = 'update_connection'

        if params.id and cherrypy.request.path_info == self.path + '/view':
            params.load_counter = 2
        elif params.m2o_model:
            if params.context is None:
                params.context = {'m2o_model': params.m2o_model}
            else:
                params.context.update({'m2o_model': params.m2o_model})

        proxy_field = rpc.RPCProxy('ir.model.fields')
        field_ids = proxy_field.search([('ttype', '=', 'many2one'),
                                        ('model', '=', params.model),
                                        ('relation', '=', params.context.get('m2o_model', ''))])

        fields = map(lambda field: field['name'],
                     proxy_field.read(field_ids, ['name'],
                                      rpc.get_session().context))

        connector = rpc.RPCProxy(params.model).read(params.id, fields,
                                                    rpc.get_session().context)

        params.hidden_fields = [
            tw.form.Hidden(name=fields[0], default=connector[fields[0]][0]),
            tw.form.Hidden(name=fields[1], default=connector[fields[1]][0]),
            tw.form.Hidden(name='_terp_m2o_model', default=params.m2o_model)]

        form = self.create_form(params, tg_errors)

        field_act_from = form.screen.widget.get_widgets_by_name(fields[0])[0]
        field_act_from.set_value(params.start or False)
        field_act_from.readonly = True

        field_act_to = form.screen.widget.get_widgets_by_name(fields[1])[0]
        field_act_to.set_value(params.end or False)
        field_act_to.readonly = True

        vals = getattr(cherrypy.request, 'terp_validators', {})
        vals[fields[0]] = validators.Int()
        vals[fields[1]] = validators.Int()

        return dict(form=form, params=params)

    @expose()
    def edit(self, **kw):
        params, data = TinyDict.split(kw)

        if not params.model:
            params.update(kw)

        params.view_mode = ['form']
        params.view_type = 'form'
        params.editable = True

        return self.create(params)

    @expose('json', methods=('POST',))
    def delete(self, conn_obj, id, **kw):
        error_msg = None
        proxy = rpc.RPCProxy(conn_obj)
        res_tr = proxy.unlink(int(id))

        if not res_tr:
            error_msg = _('Could not delete state')

        return dict(error=error_msg)

    @expose('json')
    def auto_create(self, conn_obj, src, des, act_from, act_to, **kw):
        conn_flds = eval(kw.get('conn_flds', '[]'))
        conn_flds_string = eval(kw.get('conn_flds_string', '[]'))
        proxy_tr = rpc.RPCProxy(conn_obj)

        if not(kw.get('id', False)):
            id = proxy_tr.create({src: act_from, des: act_to})
        else:
            id = int(kw['id'])

        if src not in conn_flds: conn_flds.append(src)
        if des not in conn_flds: conn_flds.append(des)

        result = proxy_tr.read(id, conn_flds, rpc.get_session().context)

        data = {
            'id': result['id'],
            's_id': result[src][0],
            'd_id': result[des][0],
            'source': result[src][1],
            'destination': result[des][1],
            'options': {}
        }

        for i, fld in enumerate(conn_flds):
            data['options'][conn_flds_string[i]] = result[fld]

        if id > 0:
            return {'flag': True, 'data': data}
        else:
            return {'flag': False}

    @expose('json')
    def get_info(self, conn_obj, id, **kw):
        proxy_tr = rpc.RPCProxy(conn_obj)
        search_tr = proxy_tr.search([('id', '=', int(id))], 0, 0, 0, rpc.get_session().context)
        data = proxy_tr.read(search_tr, [], rpc.get_session().context)

        return dict(data=data[0])

    @expose('json', methods=('POST',))
    def change_ends(self, conn_obj, id, field, value):
        proxy_tr = rpc.RPCProxy(conn_obj)
        proxy_tr.write([int(id)], {field: int(value)}, rpc.get_session().context)
        return dict()


class Workflow(Form):

    _cp_path = "/view_diagram/workflow"

    @expose(template="/openerp/controllers/templates/form.mako")
    def index(self, model, rec_id=None):

        proxy = rpc.RPCProxy("workflow")
        result = proxy.get_active_workitems(model, rec_id)
        wkf = result['wkf']

        if not wkf:
            raise common.message(_('No workflow associated!'))

        params = TinyDict()
        params.update(
            _terp_view_type='diagram',
            _terp_model='workflow',
            _terp_ids=[wkf['id']],
            _terp_editable=True,
            _terp_id=wkf['id'],
            _terp_view_mode=['tree', 'form', 'diagram']
        )
        return self.create(params)


    @expose('json')
    def get_info(self, id, model, node_obj, conn_obj, src_node, des_node, **kw):

        node_flds_visible = eval(kw.get('node_flds_v', '[]'))
        node_flds_hidden = eval(kw.get('node_flds_h', '[]'))
        node_flds_string = eval(kw.get('node_flds_string', []))
        conn_flds = eval(kw.get('conn_flds', '[]'))
        conn_flds_string = eval(kw.get('conn_flds_string', []))
        bgcolors = {}

        for color_spec in kw.get('bgcolors', '').split(';'):
            if color_spec:
                colour, test = color_spec.split(':')
                bgcolors[colour] = test

        shapes = {}
        for shape_spec in kw.get('shapes', '').split(';'):
            if shape_spec:
                colour, test = shape_spec.split(':')
                shapes[colour] = test

        proxy = rpc.RPCProxy('ir.ui.view')
        graph_search = proxy.graph_get(int(id), model, node_obj, conn_obj, src_node, des_node, False, (140, 180), rpc.get_session().context)
        nodes = graph_search['nodes']
        transitions = graph_search['transitions']
        isolate_nodes = {}

        for node in graph_search['blank_nodes']:
            isolate_nodes[node['id']] = node
        else:
            y = map(lambda t: t['y'],filter(lambda x: x['y'] if x['x']==20 else None, nodes.values()))
            y_max = (y and max(y)) or 120

        connectors = {}
        list_tr = []

        for tr in transitions:
            list_tr.append(tr)
            connectors.setdefault(tr, {
                'id': tr,
                's_id': transitions[tr][0],
                'd_id': transitions[tr][1]
            })

        proxy_tr = rpc.RPCProxy(conn_obj)
        search_trs = proxy_tr.search([('id', 'in', list_tr)], 0, 0, 0, rpc.get_session().context)
        data_trs = proxy_tr.read(search_trs, conn_flds, rpc.get_session().context)

        for tr in data_trs:
            t = connectors.get(str(tr['id']))
            t.update({
                      'source': tr[src_node][1],
                      'destination': tr[des_node][1],
                      'options': {}
                      })

            for i, fld in enumerate(conn_flds):
                t['options'][conn_flds_string[i]] = tr[fld]

        proxy_field = rpc.RPCProxy('ir.model.fields')
        field_ids = proxy_field.search([('model', '=', model), ('relation', '=', node_obj)], 0, 0, 0, rpc.get_session().context)
        field_data = proxy_field.read(field_ids, ['relation_field'], rpc.get_session().context)

        proxy_act = rpc.RPCProxy(node_obj)
        search_acts = proxy_act.search([(field_data[0]['relation_field'], '=', int(id))], 0, 0, 0, rpc.get_session().context)
        data_acts = proxy_act.read(search_acts, node_flds_hidden + node_flds_visible, rpc.get_session().context)

        for act in data_acts:
            n = nodes.get(str(act['id']))
            if not n:
                n = isolate_nodes.get(act['id'], {})
                y_max += 140
                n.update({'x': 20, 'y': y_max})
                nodes[act['id']] = n

            n.update(
                id=act['id'],
                color='white',
                shape='ellipse',
                options={}
            )

            for color, expr in bgcolors.items():
                if eval(expr, act):
                    n['color'] = color

            for shape, expr in shapes.items():
                if eval(expr, act):
                    n['shape'] = shape

            for i, fld in enumerate(node_flds_visible):
                n['options'][node_flds_string[i]] = act[fld]

        #to relate m2o field of transition to corresponding o2m in activity
        in_transition_field_id = proxy_field.search([('relation', '=', conn_obj), ('relation_field', '=', des_node), ('model', '=', node_obj)], 0, 0, 0, rpc.get_session().context)
        in_transition_field = proxy_field.read(in_transition_field_id[0], ['name'], rpc.get_session().context)['name']

        out_transition_field_id = proxy_field.search([('relation', '=', conn_obj), ('relation_field', '=', src_node), ('model', '=', node_obj)], 0, 0, 0, rpc.get_session().context)
        out_transition_field = proxy_field.read(out_transition_field_id[0], ['name'], rpc.get_session().context)['name']

        return dict(nodes=nodes, conn=connectors, in_transition_field=in_transition_field, out_transition_field=out_transition_field)
