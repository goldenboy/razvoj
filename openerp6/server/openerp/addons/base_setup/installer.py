# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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
from osv import fields, osv
import pooler
import pytz
from tools.translate import _
import tools

class base_setup_installer(osv.osv_memory):
    _name = 'base.setup.installer'
    _inherit = 'res.config.installer'

    _install_if = {
        ('sale','crm'): ['sale_crm'],
        ('sale','project'): ['project_mrp'],
    }
    _columns = {
        # Generic modules
        'crm':fields.boolean('Customer Relationship Management',
            help="Helps you track and manage relations with customers such as"
                 " leads, requests or issues. Can automatically send "
                 "reminders, escalate requests or trigger business-specific "
                 "actions based on standard events."),
        'sale':fields.boolean('Sales Management',
            help="Helps you handle your quotations, sale orders and invoicing"
                 "."),
        'project':fields.boolean('Project Management',
            help="Helps you manage your projects and tasks by tracking them, "
                 "generating plannings, etc..."),
        'knowledge':fields.boolean('Knowledge Management',
            help="Lets you install addons geared towards sharing knowledge "
                 "with and between your employees."),
        'stock':fields.boolean('Warehouse Management',
            help="Helps you manage your inventory and main stock operations: delivery orders, receptions, etc."),
        'mrp':fields.boolean('Manufacturing',
            help="Helps you manage your manufacturing processes and generate "
                 "reports on those processes."),
        'account_voucher':fields.boolean('Invoicing & Payments',
            help="Allows you to create your invoices and track the payments. It is an easier version of the accounting module for managers who are not accountants."),
        'account_accountant':fields.boolean('Accounting & Finance',
            help="Helps you handle your accounting needs, if you are not an accountant, we suggest you to install only the Invoicing "),
        'purchase':fields.boolean('Purchase Management',
            help="Helps you manage your purchase-related processes such as "
                 "requests for quotations, supplier invoices, etc..."),
        'hr':fields.boolean('Human Resources',
            help="Helps you manage your human resources by encoding your employees structure, generating work sheets, tracking attendance and more."),
        'point_of_sale':fields.boolean('Point of Sales',
            help="Helps you get the most out of your points of sales with "
                 "fast sale encoding, simplified payment mode encoding, "
                 "automatic picking lists generation and more."),
        'marketing':fields.boolean('Marketing',
            help="Helps you manage your marketing campaigns step by step."),
        'profile_tools':fields.boolean('Extra Tools',
            help="Lets you install various interesting but non-essential tools "
                "like Survey, Lunch and Ideas box."),
        'report_designer':fields.boolean('Advanced Reporting',
            help="Lets you install various tools to simplify and enhance "
                 "OpenERP's report creation."),
        # Vertical modules
        'product_expiry':fields.boolean('Food Industry',
            help="Installs a preselected set of OpenERP applications "
                "which will help you manage your industry."),
        'association':fields.boolean('Associations',
            help="Installs a preselected set of OpenERP "
                 "applications which will help you manage your association "
                 "more efficiently."),
        'auction':fields.boolean('Auction Houses',
            help="Installs a preselected set of OpenERP "
                 "applications selected to help you manage your auctions "
                 "as well as the business processes around them."),
        }

    def _if_knowledge(self, cr, uid, ids, context=None):
        if self.pool.get('res.users').browse(cr, uid, uid, context=context)\
               .view == 'simple':
            return ['document_ftp']
        return None

    def _if_misc_tools(self, cr, uid, ids, context=None):
        return ['profile_tools']

    def onchange_moduleselection(self, cr, uid, ids, *args, **kargs):
        value = {}
        # Calculate progress
        closed, total = self.get_current_progress(cr, uid)
        progress = round(100. * closed / (total + len(filter(None, args))))
        value.update({'progress':progress})
        if progress < 10.:
            progress = 10.
        
        return {'value':value}


    def execute(self, cr, uid, ids, context=None):
        module_pool = self.pool.get('ir.module.module')
        modules_selected = []
        datas = self.read(cr, uid, ids, context=context)[0]
        for mod in datas.keys():
            if mod in ('id', 'progress'):
                continue
            if datas[mod] == 1:
                modules_selected.append(mod)

        module_ids = module_pool.search(cr, uid, [('name', 'in', modules_selected)], context=context)
        need_install = False
        for module in module_pool.browse(cr, uid, module_ids, context=context):
            if module.state == 'uninstalled':
                module_pool.state_update(cr, uid, [module.id], 'to install', ['uninstalled'], context)
                need_install = True
                cr.commit()
            elif module.state == 'installed':
                cr.execute("update ir_actions_todo set state='open' \
                                    from ir_model_data as data where data.res_id = ir_actions_todo.id \
                                    and ir_actions_todo.type='special'\
                                    and data.model = 'ir.actions.todo' and data.module=%s", (module.name, ))
        if need_install:
            self.pool = pooler.restart_pool(cr.dbname, update_module=True)[1]
        return
    
base_setup_installer()

#Migrate data from another application Conf wiz

class migrade_application_installer_modules(osv.osv_memory):
    _name = 'migrade.application.installer.modules'
    _inherit = 'res.config.installer'
    _columns = {
        'import_saleforce': fields.boolean('Import Saleforce',
            help="For Import Saleforce"),
        'import_sugarcrm': fields.boolean('Import Sugarcrm',
            help="For Import Sugarcrm"),
        'sync_google_contact': fields.boolean('Sync Google Contact',
            help="For Sync Google Contact"),
        'quickbooks_ippids': fields.boolean('Quickbooks Ippids',
            help="For Quickbooks Ippids"),
    }
    
migrade_application_installer_modules()

class product_installer(osv.osv_memory):
    _name = 'product.installer'
    _inherit = 'res.config'
    _columns = {
                'customers': fields.selection([('create','Create'), ('import','Import')], 'Customers', size=32, required=True, help="Import or create customers"),

    }
    _defaults = {
                 'customers': 'create',
    }
    
    def execute(self, cr, uid, ids, context=None):
        if context is None:
             context = {}
        data_obj = self.pool.get('ir.model.data')
        val = self.browse(cr, uid, ids, context=context)[0]
        if val.customers == 'create':
            id2 = data_obj._get_id(cr, uid, 'base', 'view_partner_form')
            if id2:
                id2 = data_obj.browse(cr, uid, id2, context=context).res_id
            return {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'res.partner',
                    'views': [(id2, 'form')],
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'nodestroy':False,
                }
        if val.customers == 'import':
            return {'type': 'ir.actions.act_window'}

product_installer()


#       Define default users preferences config wiz

def _lang_get(self, cr, uid, context=None):
    obj = self.pool.get('res.lang')
    ids = obj.search(cr, uid, [('translatable','=',True)])
    res = obj.read(cr, uid, ids, ['code', 'name'], context=context)
    res = [(r['code'], r['name']) for r in res]
    return res

def _tz_get(self,cr,uid, context=None):
    return [(x, x) for x in pytz.all_timezones]

class user_preferences_config(osv.osv_memory):
    _name = 'user.preferences.config'
    _inherit = 'res.config'
    _columns = {
        'context_tz': fields.selection(_tz_get,  'Timezone', size=64,
            help="Set default for new user's timezone, used to perform timezone conversions "
                 "between the server and the client."),
        'context_lang': fields.selection(_lang_get, 'Language', required=True,
            help="Sets default language for the all user interface, when UI "
                "translations are available. If you want to Add new Language, you can add it from 'Load an Official Translation' wizard  from 'Administration' menu."),
        'view': fields.selection([('simple','Simplified'),
                                  ('extended','Extended')],
                                 'Interface', required=True, help= "If you use OpenERP for the first time we strongly advise you to select the simplified interface, which has less features but is easier. You can always switch later from the user preferences." ),
        'menu_tips': fields.boolean('Display Tips', help="Check out this box if you want to always display tips on each menu action"),
                                 
    }
    _defaults={
               'view' : lambda self,cr,uid,*args: self.pool.get('res.users').browse(cr, uid, uid).view or 'simple',
               'context_lang' : 'en_US',
               'menu_tips' : True
    }
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(user_preferences_config, self).default_get(cr, uid, fields, context=context)
        res_default = self.pool.get('ir.values').get(cr, uid, 'default', False, ['res.users'])
        for id, field, value in res_default:
            res.update({field: value})
        return res

    def execute(self, cr, uid, ids, context=None):
        user_obj = self.pool.get('res.users')
        user_ids = user_obj.search(cr, uid, [], context=context)
        for o in self.browse(cr, uid, ids, context=context):
            user_obj.write(cr , uid, user_ids ,{'context_tz' : o.context_tz, 'context_lang' : o.context_lang, 'view' : o.view, 'menu_tips' : o.menu_tips}, context=context)
            ir_values_obj = self.pool.get('ir.values')
            ir_values_obj.set(cr, uid, 'default', False, 'context_tz', ['res.users'], o.context_tz)
            ir_values_obj.set(cr, uid, 'default', False, 'context_lang', ['res.users'], o.context_lang)
            ir_values_obj.set(cr, uid, 'default', False, 'view', ['res.users'], o.view)
            ir_values_obj.set(cr, uid, 'default', False, 'menu_tips', ['res.users'], o.menu_tips)
        return {}

user_preferences_config()

# Specify Your Terminology

class specify_partner_terminology(osv.osv_memory):
    _name = 'specify.partner.terminology'
    _inherit = 'res.config'
    _columns = {
        'partner': fields.selection([('Customer','Customer'),
                                  ('Client','Client'),
                                  ('Member','Member'),
                                  ('Patient','Patient'),
                                  ('Partner','Partner'),
                                  ('Donor','Donor'),
                                  ('Guest','Guest'),
                                  ('Tenant','Tenant')
                                  ],
                                 'Choose how to call a customer', required=True ),
    }
    _defaults={
               'partner' :'Partner',
    }
    
    def make_translations(self, cr, uid, ids, name, type, src, value, res_id=0, context=None):
        trans_obj = self.pool.get('ir.translation')
        user_obj = self.pool.get('res.users')
        context_lang = user_obj.browse(cr, uid, uid, context=context).context_lang
        existing_trans_ids = trans_obj.search(cr, uid, [('name','=',name), ('lang','=',context_lang), ('type','=',type), ('src','=',src), ('res_id','=',res_id)])
        if existing_trans_ids:
            trans_obj.write(cr, uid, existing_trans_ids, {'value': value}, context=context)
        else:
            create_id = trans_obj.create(cr, uid, {'name': name,'lang': context_lang, 'type': type, 'src': src, 'value': value , 'res_id': res_id}, context=context)
        return {}
    
    def execute(self, cr, uid, ids, context=None):
        def _case_insensitive_replace(ref_string, src, value):
            import re
            pattern = re.compile(src, re.IGNORECASE)
            return pattern.sub(_(value), _(ref_string))
        trans_obj = self.pool.get('ir.translation')
        fields_obj = self.pool.get('ir.model.fields')
        menu_obj = self.pool.get('ir.ui.menu')
        act_window_obj = self.pool.get('ir.actions.act_window')
        for o in self.browse(cr, uid, ids, context=context):
            #translate label of field
            field_ids = fields_obj.search(cr, uid, [('field_description','ilike','Customer')])
            for f_id in fields_obj.browse(cr ,uid, field_ids, context=context):
                field_ref = f_id.model_id.model + ',' + f_id.name
                self.make_translations(cr, uid, ids, field_ref, 'field', f_id.field_description, _case_insensitive_replace(f_id.field_description,'Customer',o.partner), context=context)
            #translate help tooltip of field
            for obj in self.pool.obj_pool.values():
                for field_name, field_rec in obj._columns.items():
                    if field_rec.help.lower().count('customer'):
                        field_ref = obj._name + ',' + field_name
                        self.make_translations(cr, uid, ids, field_ref, 'help', field_rec.help, _case_insensitive_replace(field_rec.help,'Customer',o.partner), context=context)
            #translate menuitems
            menu_ids = menu_obj.search(cr,uid, [('name','ilike','Customer')])
            for m_id in menu_obj.browse(cr, uid, menu_ids, context=context):
                menu_name = m_id.name
                menu_ref = 'ir.ui.menu' + ',' + 'name'
                self.make_translations(cr, uid, ids, menu_ref, 'model', menu_name, _case_insensitive_replace(menu_name,'Customer',o.partner), res_id=m_id.id, context=context)
            #translate act window name
            act_window_ids = act_window_obj.search(cr, uid, [('name','ilike','Customer')])
            for act_id in act_window_obj.browse(cr ,uid, act_window_ids, context=context):
                act_ref = 'ir.actions.act_window' + ',' + 'name'
                self.make_translations(cr, uid, ids, act_ref, 'model', act_id.name, _case_insensitive_replace(act_id.name,'Customer',o.partner), res_id=act_id.id, context=context)
            #translate act window tooltips
            act_window_ids = act_window_obj.search(cr, uid, [('help','ilike','Customer')])
            for act_id in act_window_obj.browse(cr ,uid, act_window_ids, context=context):
                act_ref = 'ir.actions.act_window' + ',' + 'help'
                self.make_translations(cr, uid, ids, act_ref, 'model', act_id.help, _case_insensitive_replace(act_id.help,'Customer',o.partner), res_id=act_id.id, context=context)
        return {}
    
specify_partner_terminology()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
