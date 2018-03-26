# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.tools import float_is_zero

class PosOrder(models.Model):
    _inherit = "pos.order"
    _description = "Pos Return"
    
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
    def create_return_order(self,order,journal_id):
        order.update({
                'is_return':True
            })  
        order = self.create(order)
        order.add_payment({
                'amount':order.amount_total,
                'payment_date': fields.Datetime.now(),
                'payment_name': _('Payment Refunded'),
                'journal':journal_id,
            })
        order.action_pos_order_paid()
        report = self.env['report'].get_action(order, 'pos_order.receipt_report')
        return report
          