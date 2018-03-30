# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.tools import float_is_zero

class PosOrder(models.Model):
    _inherit = "pos.order"
    _description = "Pos Return"
    
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
          