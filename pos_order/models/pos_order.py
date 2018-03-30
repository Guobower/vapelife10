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
    
    is_return = fields.Boolean("Is return Order?",help="This is mark a return order for filtering")
    
    # Tick is_return = True to mark a return order    
    @api.multi
    def refund(self):
        """Create a copy of order  for refund order"""
        PosOrder = self.env['pos.order']
        current_session = self.env['pos.session'].search([('state', '!=', 'closed'), ('user_id', '=', self.env.uid)], limit=1)
        if not current_session:
            raise UserError(_('To return product(s), you need to open a session that will be used to register the refund.'))
        for order in self:
            clone = order.copy({
                # ot used, name forced by create
                'name': order.name + _(' REFUND'),
                'session_id': current_session.id,
                'date_order': fields.Datetime.now(),
                'pos_reference': order.pos_reference,
                'is_return':True,
            })
            PosOrder += clone

        for clone in PosOrder:
            for order_line in clone.lines:
                order_line.write({'qty': -order_line.qty})
        return {
            'name': _('Return Products'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order',
            'res_id': PosOrder.ids[0],
            'view_id': False,
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }        
    
    @api.model
    def search_order(self,org_query):
        org_query = re.sub(r"[\[\]\(\)\+\*\?\.\!\&\^\$\|\~\_\{\}\:\,\\\/]",".",org_query)
        orders_search = self.search_read([('pos_reference','ilike',org_query)],_LIST_FIELDS)
        return orders_search
