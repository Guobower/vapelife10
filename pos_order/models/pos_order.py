# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
import re
_LIST_FIELDS = [
    'id', 'name', 'session_id', 'pos_reference', 'partner_id',
    'amount_total', 'amount_tax','note','state',
    'amount_paid','date_order','balance'
    ]

class PosOrder(models.Model):
    _inherit = "pos.order"
    _description =  "Order methods for POS"
    
    @api.model
    def search_order(self,org_query):
        org_query = re.sub(r"[\[\]\(\)\+\*\?\.\!\&\^\$\|\~\_\{\}\:\,\\\/]",".",org_query)
        orders_search = self.search_read([('pos_reference','ilike',org_query)],_LIST_FIELDS)
        return orders_search
