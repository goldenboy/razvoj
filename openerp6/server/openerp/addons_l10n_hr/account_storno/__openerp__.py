# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Module: account_storno
#    Author: Goran Kliska
#    mail:   gkliskaATgmail.com
#    Copyright (C) 2011- Slobodni programi d.o.o., Zagreb
#    Contributions: 
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

#import 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

{
    "name" : "Account storno",
    "description" : """

Author: Goran Kliska @ Slobodni programi d.o.o.
Contributions: 

Description:
 Enables storno accounting.
 Adds new field storno_or_contra on the Journal. 

TODO :


""",
    "version" : "11.1",
    "author" : "Slobodni programi d.o.o.",
    "category" : "Localisation/Croatia",
    "website": "http://www.slobodni-programi.hr",

    'depends': [
                'account',
                ],
    'init_xml': [],
    'update_xml': [
                   ],
    "demo_xml" : [],
    'test' : [],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: