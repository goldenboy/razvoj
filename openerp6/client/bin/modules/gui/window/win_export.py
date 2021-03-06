# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import gtk
from gtk import glade
import gobject
import gettext
import common

import rpc

import service
import types
import os

def export_csv(fname, fields, result, write_title=False):
    import csv
    try:
        fp = file(fname, 'wb+')
        writer = csv.writer(fp, quoting=csv.QUOTE_ALL)
        if write_title:
            writer.writerow(fields)
        for data in result:
            row = []
            for d in data:
                if type(d)==types.StringType:
                    row.append(d.replace('\n',' ').replace('\t',' '))
                else:
                    row.append(d or '')
            writer.writerow(row)
        fp.close()
        common.message(str(len(result))+_(' record(s) saved !'))
        return True
    except IOError, (errno, strerror):
        common.message(_("Operation failed !\nI/O error")+"(%s)" % (errno,))
        return False

def open_excel(fields, result):
    if os.name == 'nt':
        try:
            if len(fields) > 0:
                from win32com.client import Dispatch
                import pywintypes
                xlApp = Dispatch("Excel.Application")
                xlApp.Workbooks.Add()
                for col in range(len(fields)):
                    xlApp.ActiveSheet.Cells(1,col+1).Value = fields[col]
                sht = xlApp.ActiveSheet
                for a in result:
                    for b in range(len(a)):
                        if type(a[b]) == type(''):
                            a[b]=a[b].decode('utf-8','replace')
                        elif type(a[b]) == type([]):
                            if len(a[b])==2:
                                a[b] = a[b][1].decode('utf-8','replace')
                            else:
                                a[b] = ''
                sht.Range(sht.Cells(2, 1), sht.Cells(len(result)+1, len(fields))).Value = result
                xlApp.Visible = 1
        except:
            common.error(_('Error Opening Excel !'),'')
    else:
#        common.message(_("Function only available for MS Office !\nSorry, OOo users :("))
        try:
            import subprocess
            import time
            retcode = subprocess.call(["soffice", "-accept=socket,host=localhost,port=2002;urp;", "-nodefault"], shell=False)
            from oootools import OOoTools
            for i in range(10):
                ooo = OOoTools('localhost', 2002)
                if ooo and ooo.desktop:
                    break
                time.sleep(1)
            doc = ooo.desktop.loadComponentFromURL("private:factory/scalc",'_blank',0,())
            sheet = doc.CurrentController.ActiveSheet
            for col in range(len(fields)):
                cell = sheet.getCellByPosition(col, 0)
                cell.String = fields[col]
            if len(fields) > 0:
                cellrange = sheet.getCellRangeByPosition(0, 1, len(fields) - 1, len(result))
                tresult = []
                for i in range(len(result)):
                    tresult.append(tuple(result[i]))
                    tresult = tuple(tresult)
                cellrange.setDataArray(tresult)
        except:
            common.error(_('Error Opening Excel !'),'')

def datas_read(ids, model, fields, fields_view, prefix='', context=None):
    ctx = context.copy()
    ctx.update(rpc.session.context)
    datas = rpc.session.rpc_exec_auth('/object', 'execute', model, 'export_data', ids, fields, ctx)
    return datas

class win_export(object):
    def __init__(self, model, ids, fields, preload = [], parent=None, context=None):
        self.glade = glade.XML(common.terp_path("openerp.glade"), 'win_save_as',
                gettext.textdomain())
        self.win = self.glade.get_widget('win_save_as')
        self.ids = ids
        self.model = model
        self.fields_data = {}
        self.fields = {}
        if context is None:
            context = {}
        self.context = context

        if parent is None:
            parent = service.LocalService('gui.main').window
        self.win.set_transient_for(parent)
        self.win.set_icon(common.OPENERP_ICON)
        self.parent = parent

        self.view1 = gtk.TreeView()
        self.view1.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.glade.get_widget('exp_vp1').add(self.view1)
        self.view2 = gtk.TreeView()
        self.view2.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.glade.get_widget('exp_vp2').add(self.view2)
        self.view1.set_headers_visible(False)
        self.view2.set_headers_visible(False)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_('Field Name'), cell, text=0, background=2)
        self.view1.append_column(column)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_('Field Name'), cell, text=0)
        self.view2.append_column(column)

        #for f in preload:
        #    self.model2.set(self.model2.append(), 0, f[1], 1, f[0])
        self.wid_import_compatible = self.glade.get_widget('import_compatible')

        self.model1 = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.model2 = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)

        self.fields_original = fields
        self.model_populate(self.fields_original)

        self.view1.set_model(self.model1)
        self.view2.set_model(self.model2)
        self.view1.show_all()
        self.view2.show_all()

        hbox = self.glade.get_widget('hbox55')
        self.wid_action = gtk.combo_box_new_text()
        self.wid_action.append_text(_('Open in Excel'))
        self.wid_action.append_text(_('Save as CSV'))
        hbox.pack_start(self.wid_action)
        hbox.reorder_child(self.wid_action, 0)
        hbox.show_all()
        action = self.wid_action.set_active(os.name != 'nt')

        self.wid_write_field_names = self.glade.get_widget('add_field_names_cb')

        if os.name != 'nt':
            self.wid_action.remove_text(0)
        else:
            try:
                from win32com.client import Dispatch
                import pywintypes
                xlApp = Dispatch("Excel.Application")
            except Exception,e:
                if isinstance(e, pywintypes.com_error):
                    action = self.wid_action.set_active(isinstance(e, pywintypes.com_error))
                    self.wid_action.remove_text(0)
                else:
                    pass

        self.glade.signal_connect('on_but_unselect_all_clicked', self.sig_unsel_all)
        self.glade.signal_connect('on_but_select_all_clicked', self.sig_sel_all)
        self.glade.signal_connect('on_but_select_clicked', self.sig_sel)
        self.glade.signal_connect('on_but_unselect_clicked', self.sig_unsel)
        self.glade.signal_connect('on_but_predefined_clicked', self.add_predef)
        self.glade.signal_connect('on_but_delpredefined_clicked', self.del_export_list_btn)
        self.glade.signal_connect('on_import_toggled', self.import_toggled)

        # Creating the predefined export view
        self.pref_export = gtk.TreeView()
        self.pref_export.append_column(gtk.TreeViewColumn('Export name', gtk.CellRendererText(), text=1))
        self.pref_export.append_column(gtk.TreeViewColumn('Exported fields', gtk.CellRendererText(), text=2))
        self.glade.get_widget('predefined_exports').add(self.pref_export)

        self.pref_export.connect("row-activated", self.sel_predef)
        self.pref_export.connect('key_press_event', self.del_export_list_key)

        # Fill the predefined export tree view and show everything
        self.fill_predefwin()
        self.pref_export.show_all()

    def model_populate(self, fields, prefix_node='', prefix=None, prefix_value='', level=2):
        import_comp = self.wid_import_compatible.get_active()
        fields = fields.copy()
        fields.update({'id':{'string':_('ID')}})
        fields.update({'.id':{'string':_('Database ID')}})

        fields_order = fields.keys()
        fields_order.sort(lambda x,y: -cmp(fields[x].get('string', ''), fields[y].get('string', '')))
        for field in fields_order:
            if import_comp and fields[field].get('readonly', False):
                ok = False
                for sl in fields[field].get('states', {}).values():
                    for s in sl:
                        ok = ok or (s==('readonly',False))
                if not ok: continue
            self.fields_data[prefix_node+field] = fields[field]
            if prefix_node:
                self.fields_data[prefix_node + field]['string'] = '%s%s' % (prefix_value, self.fields_data[prefix_node + field]['string'])
            st_name = fields[field]['string'] or field
            node = self.model1.insert(prefix, 0, [st_name, prefix_node+field, (fields[field].get('required', False) and '#ddddff') or 'white'])
            self.fields[prefix_node+field] = (st_name, fields[field].get('relation', False))
            if fields[field].get('relation', False) and level>0:
                if (fields[field]['type'] in ['many2many']) and import_comp:
                    pass
                else:
                    if (not import_comp) or (fields[field]['type'] in ['one2many']):
                        fields2 = rpc.session.rpc_exec_auth('/object', 'execute', fields[field]['relation'], 'fields_get', False, rpc.session.context)
                        self.model_populate(fields2, prefix_node+field+'/', node, st_name+'/', level-1)
                    else:
                        self.model_populate({}, prefix_node+field+'/', node, st_name+'/', level-1)

    def del_export_list_key(self,widget, event, *args):
        if event.keyval==gtk.keysyms.Delete:
            self.del_selected_export_list()

    def del_export_list_btn(self, widget=None):
        self.del_selected_export_list()

    def del_selected_export_list(self):
        store, paths = self.pref_export.get_selection().get_selected_rows()
        for p in paths:
            export_fields= store.get_value(store.__getitem__(p[0]).iter,0)
            export_name= store.get_value(store.__getitem__(p[0]).iter,1)

            ir_export = rpc.RPCProxy('ir.exports')
            ir_export_line = rpc.RPCProxy('ir.exports.line')

            export_ids=ir_export.search([('name','=',export_name)])

            for id in export_ids:
                fields=[]
                line_ids=ir_export_line.search([('export_id','=',id)])

                obj_line=ir_export_line.read(line_ids)
                for i in range(0,len(obj_line)):
                    fields.append(obj_line[i]['name'])

                if fields==export_fields:
                    ir_export.unlink(id)
                    ir_export_line.unlink(line_ids)
                    store.remove(store.get_iter(p))
                    break

    def sig_sel_all(self, widget=None):
        self.model2.clear()
        for field, relation in self.fields.keys():
            if not relation:
                self.model2.set(self.model2.append(), 0, self.fields[field], 1, field)

    def sig_sel(self, widget=None):
        sel = self.view1.get_selection()
        sel.selected_foreach(self._sig_sel_add)

    def _sig_sel_add(self, store, path, iter):
        name, relation = self.fields[store.get_value(iter,1)]
        #if relation:
        #    return
        num = self.model2.append()
        self.model2.set(num, 0, store.get_value(iter,0), 1, store.get_value(iter,1))

    def sig_unsel(self, widget=None):
        store, paths = self.view2.get_selection().get_selected_rows()
        for p in paths:
            store.remove(store.get_iter(p))

    def import_toggled(self, widget=None):
        self.model1.clear()
        self.model2.clear()
        self.model_populate(self.fields_original)

    def sig_unsel_all(self, widget=None):
        self.model2.clear()

    def fill_predefwin(self):
        self.predef_model = gtk.ListStore(gobject.TYPE_PYOBJECT, gobject.TYPE_STRING, gobject.TYPE_STRING)
        ir_export = rpc.RPCProxy('ir.exports')
        ir_export_line = rpc.RPCProxy('ir.exports.line')
        export_ids = ir_export.search([('resource', '=', self.model)])
        for export in ir_export.read(export_ids):
            fields = ir_export_line.read(export['export_fields'])
            try:
                self.predef_model.append(([f['name'] for f in fields], export['name'], ', '.join([self.fields_data[f['name']]['string'] for f in fields])))
            except:
                pass
        self.pref_export.set_model(self.predef_model)

    def add_predef(self, button):
        name = common.ask(_('What is the name of this export ?'))
        if not name:
            return
        ir_export = rpc.RPCProxy('ir.exports')
        iter = self.model2.get_iter_root()
        fields = []
        while iter:
            field_name = self.model2.get_value(iter, 1)
            fields.append(field_name)
            iter = self.model2.iter_next(iter)
        ir_export.create({'name' : name, 'resource' : self.model, 'export_fields' : [(0, 0, {'name' : f}) for f in fields]})
        self.predef_model.append((fields, name, ','.join([self.fields_data[f]['string'] for f in fields])))

    def sel_predef(self, treeview, path, column):
        self.model2.clear()
        for field in self.predef_model[path[0]][0]:
            self.model2.append((self.fields_data[field]['string'], field))

    def go(self):
        button = self.win.run()
        if button==gtk.RESPONSE_OK:
            fields = []
            fields2 = []
            iter = self.model2.get_iter_root()
            while iter:
                fields.append(self.model2.get_value(iter, 1).replace('/.id','.id'))
                fields2.append(self.model2.get_value(iter, 0))
                iter = self.model2.iter_next(iter)
            action = self.wid_action.get_active_text()
            self.parent.present()
            self.win.destroy()
            import_comp = self.wid_import_compatible.get_active()
            result = datas_read(self.ids, self.model, fields, self.fields_data, context=self.context)
            if result.get('warning',False):
                common.message_box(_('Exportation Error !'), unicode(result.get('warning',False)))
                return False
            result = result.get('datas',[])
            if import_comp:
                fields2 = fields
            if action == _('Open in Excel'):
                open_excel(fields2, result)
            else:
                fname = common.file_selection(_('Save As...'),
                        parent=self.parent, action=gtk.FILE_CHOOSER_ACTION_SAVE)
                if fname:
                    export_csv(fname, fields2, result, self.wid_write_field_names.get_active())
            return True
        else:
            self.parent.present()
            self.win.destroy()
            return False




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

