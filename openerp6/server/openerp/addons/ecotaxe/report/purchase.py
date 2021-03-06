#!/usr/bin/env python
#coding: utf-8

# (c) 2007 Sednacom <http://www.sednacom.fr>
# authors : Gaël <gael@sednacom.fr>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import time
from report import report_sxw

class purchase_order(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(purchase_order, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
		})
report_sxw.report_sxw('report.purchase.order.ecotaxe', 'purchase.order', 'addons/ecotaxe/report/purchase.rml', parser=purchase_order)
