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

from osv import fields, osv
from crm import crm
import time
import binascii
import tools
from tools.translate import _

CRM_CLAIM_PENDING_STATES = (
    crm.AVAILABLE_STATES[2][0], # Cancelled
    crm.AVAILABLE_STATES[3][0], # Done
    crm.AVAILABLE_STATES[4][0], # Pending
)


class crm_claim(crm.crm_case, osv.osv):
    """
    Crm claim
    """
    _name = "crm.claim"
    _description = "Claim"
    _order = "priority,date desc"
    _inherit = ['mailgate.thread']
    _columns = {
        'id': fields.integer('ID', readonly=True), 
        'name': fields.char('Claim Subject', size=128, required=True), 
        'action_next': fields.char('Next Action', size=200),
        'date_action_next': fields.datetime('Next Action Date'),
        'description': fields.text('Description'), 
        'resolution': fields.text('Resolution'), 
        'create_date': fields.datetime('Creation Date' , readonly=True), 
        'write_date': fields.datetime('Update Date' , readonly=True), 
        'date_deadline': fields.date('Deadline'), 
        'date_closed': fields.datetime('Closed', readonly=True), 
        'date': fields.datetime('Claim Date'), 
        'ref' : fields.reference('Reference', selection=crm._links_get, size=128), 
        'categ_id': fields.many2one('crm.case.categ', 'Category', \
                            domain="[('section_id','=',section_id),\
                            ('object_id.model', '=', 'crm.claim')]"), 
        'priority': fields.selection(crm.AVAILABLE_PRIORITIES, 'Priority'), 
        'type_action': fields.selection([('correction','Corrective Action'),('prevention','Preventive Action')], 'Action Type'),
        'user_id': fields.many2one('res.users', 'Responsible'), 
        'user_fault': fields.char('Trouble Responsible', size=64), 
        'section_id': fields.many2one('crm.case.section', 'Sales Team', \
                        select=True, help="Sales team to which Case belongs to."\
                                "Define Responsible user and Email account for"\
                                " mail gateway."), 
        'company_id': fields.many2one('res.company', 'Company'), 
        'partner_id': fields.many2one('res.partner', 'Partner'), 
        'partner_address_id': fields.many2one('res.partner.address', 'Partner Contact', \
                                # domain="[('partner_id','=',partner_id)]"
                                 ), 
        'email_cc': fields.text('Watchers Emails', size=252, help="These email addresses will be added to the CC field of all inbound and outbound emails for this record before being sent. Separate multiple email addresses with a comma"), 
        'email_from': fields.char('Email', size=128, help="These people will receive email."), 
        'partner_phone': fields.char('Phone', size=32), 
        'stage_id': fields.many2one ('crm.case.stage', 'Stage', domain="[('section_ids','=',section_id)]"), 
        'cause': fields.text('Root Cause'), 
        'state': fields.selection(crm.AVAILABLE_STATES, 'State', size=16, readonly=True, 
                                  help='The state is set to \'Draft\', when a case is created.\
                                  \nIf the case is in progress the state is set to \'Open\'.\
                                  \nWhen the case is over, the state is set to \'Done\'.\
                                  \nIf the case needs to be reviewed then the state is set to \'Pending\'.'), 
        'message_ids': fields.one2many('mailgate.message', 'res_id', 'Messages', domain=[('model','=',_name)]),
    }

    _defaults = {
        'user_id': crm.crm_case._get_default_user, 
        'partner_id': crm.crm_case._get_default_partner, 
        'partner_address_id': crm.crm_case._get_default_partner_address, 
        'email_from':crm.crm_case. _get_default_email, 
        'state': lambda *a: 'draft', 
        'section_id': crm.crm_case._get_section, 
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'crm.case', context=c), 
        'priority': lambda *a: crm.AVAILABLE_PRIORITIES[2][0],
    }
    
    def onchange_partner_id(self, cr, uid, ids, part, email=False):
        """This function returns value of partner address based on partner
        @param part: Partner's id
        @email: Partner's email ID
        """
        if not part:
            return {'value': {'partner_address_id': False,
                            'email_from': False, 
                            'partner_phone': False,
                            'partner_mobile': False
                            }}
        addr = self.pool.get('res.partner').address_get(cr, uid, [part], ['contact'])
        data = {'partner_address_id': addr['contact']}
        data.update(self.onchange_partner_address_id(cr, uid, ids, addr['contact'])['value'])
        return {'value': data}

    def onchange_partner_address_id(self, cr, uid, ids, add, email=False):
        """This function returns value of partner email based on Partner Address
        @param add: Id of Partner's address
        @email: Partner's email ID
        """
        if not add:
            return {'value': {'email_from': False}}
        address = self.pool.get('res.partner.address').browse(cr, uid, add)
        return {'value': {'email_from': address.email, 'partner_phone': address.phone, 'partner_mobile': address.mobile}}

    def case_open(self, cr, uid, ids, *args):
        for l in self.browse(cr, uid, ids):
            # When coming from draft override date and stage otherwise just set state
            if l.state == 'draft':
                message = _("The claim '%s' has been opened.") % l.name
                self.log(cr, uid, l.id, message)
                value = {'date_open': time.strftime('%Y-%m-%d %H:%M:%S')}
                self.write(cr, uid, [l.id], value)
                stage_id = self.stage_find(cr, uid, l.section_id.id or False, [('sequence','>',0)])
                if stage_id:
                    self.stage_set(cr, uid, [l.id], stage_id)
        res = super(crm_claim, self).case_open(cr, uid, ids, *args)
        return res
    
    def message_new(self, cr, uid, msg, context=None):
        """ Automatically calls when new email message arrives
        """
        mailgate_pool = self.pool.get('email.server.tools')

        subject = msg.get('subject') or _("No Subject")
        body = msg.get('body')
        msg_from = msg.get('from')
        priority = msg.get('priority')

        vals = {
            'name': subject,
            'email_from': msg_from,
            'email_cc': msg.get('cc'),
            'description': body,
            'user_id': False,
        }
        if msg.get('priority', False):
            vals['priority'] = priority

        res = mailgate_pool.get_partner(cr, uid, msg.get('from') or msg.get_unixfrom())
        if res:
            vals.update(res)

        res = self.create(cr, uid, vals, context)
        attachents = msg.get('attachments', [])
        for attactment in attachents or []:
            data_attach = {
                'name': attactment,
                'datas':binascii.b2a_base64(str(attachents.get(attactment))),
                'datas_fname': attactment,
                'description': 'Mail attachment',
                'res_model': self._name,
                'res_id': res,
            }
            self.pool.get('ir.attachment').create(cr, uid, data_attach)

        return res

    def message_update(self, cr, uid, ids, vals={}, msg="", default_act='pending', context=None):
        """
        @param ids: List of update mail’s IDs 
        """
        if isinstance(ids, (str, int, long)):
            ids = [ids]

        if msg.get('priority') in dict(crm.AVAILABLE_PRIORITIES):
            vals['priority'] = msg.get('priority')

        maps = {
            'cost':'planned_cost',
            'revenue': 'planned_revenue',
            'probability':'probability'
        }
        vls = {}
        for line in msg['body'].split('\n'):
            line = line.strip()
            res = tools.misc.command_re.match(line)
            if res and maps.get(res.group(1).lower()):
                key = maps.get(res.group(1).lower())
                vls[key] = res.group(2).lower()
        vals.update(vls)

        # Unfortunately the API is based on lists
        # but we want to update the state based on the
        # previous state, so we have to loop:
        for case in self.browse(cr, uid, ids, context=context):
            values = dict(vals)
            if case.state in CRM_CLAIM_PENDING_STATES:
                values.update(state=crm.AVAILABLE_STATES[1][0]) #re-open
            res = self.write(cr, uid, [case.id], values, context=context)
        return res

    def msg_send(self, cr, uid, id, *args, **argv):
        """ Send The Message
        @param ids: List of email’s IDs
        """
        return True

crm_claim()

class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'claims_ids': fields.one2many('crm.claim', 'partner_id', 'Claims'),
    }
res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
