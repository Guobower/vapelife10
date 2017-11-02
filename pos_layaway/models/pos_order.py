# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.tools import float_is_zero

class PosOrder(models.Model):
    _inherit = "pos.order"
    _description = "Pos Layaway"
    
    @api.multi
    def make_layaway_payment(self,amount_paid,journal_id):
        amount = 0.00
        msg = ""
        change = 0.00
        if (amount_paid > self.balance) or (amount_paid == self.balance):
            amount = self.balance
            change = amount_paid - self.balance
        else:
            amount = amount_paid
            msg = _("Payment registered successfully")
        
        self.add_payment({
                        'amount':amount, 
                        'payment_date': fields.Datetime.now(),
                        'payment_name': _('Layaway Payment Installment'),                            
                        'journal':journal_id,
                    })
        if self.test_paid():
            msg = _("Payment registered successfully. Inventory Released")
            self.action_pos_order_paid()
            self.stock_reserve_ids.release()
        
        return {
                'msg':' | '.join([msg,"Change: %s"%(change)]),
                'state':self.state,
                'balance':self.balance,
                'amount_paid':self.amount_paid,
            }
    
    @api.depends('statement_ids', 'lines.price_subtotal_incl', 'lines.discount')
    def _compute_amount_all(self):
        for order in self:
            order.amount_paid = order.amount_return = order.amount_tax = 0.0
            currency = order.pricelist_id.currency_id
            order.amount_paid = sum(payment.amount for payment in order.statement_ids)
            order.amount_return = sum(payment.amount < 0 and payment.amount or 0 for payment in order.statement_ids)
            order.amount_tax = currency.round(sum(self._amount_line_tax(line, order.fiscal_position_id) for line in order.lines))
            amount_untaxed = currency.round(sum(line.price_subtotal for line in order.lines))
            order.amount_total = order.amount_tax + amount_untaxed    
            order.balance = order.amount_total - order.amount_paid
    
    @api.model
    def create_layaway_order(self,order):
        pos_order = self._process_order(order)
        pos_order.write({'state':'layaway'})
        for line in pos_order.lines.filtered(lambda l: l.product_id.type in ['product', 'consu'] and not float_is_zero(l.qty, precision_digits=l.product_id.uom_id.rounding)):
            stock_reservation = self.env['stock.reservation'].create({
                'product_id':line.product_id.id,
                'product_uom_qty':line.qty,
                'product_uom':line.product_id.uom_id.id,
                'name':line.product_id.name,
                'order_id':pos_order.id,
                'note':pos_order.pos_reference,
            })
            stock_reservation.reserve()
        if order.get('amount_paid',0) > 0 and order.get('journal_id',False):
            pos_order.add_payment({
                            'amount':order['amount_paid'], 
                            'payment_date': fields.Datetime.now(),
                            'payment_name': _('Upfront Layaway amount'),                            
                            'journal':order['journal_id']
                        })
        return pos_order.id
    
    state = fields.Selection(selection_add = [('layaway','Layaway')])
    stock_reserve_ids = fields.One2many('stock.reservation','order_id','Stock Reservation')
    balance = fields.Float(compute='_compute_amount_all', string='Balance',readonly=True, digits=0)
    
    
class StockReservation(models.Model):
    _inherit = "stock.reservation"
    _description = "Stock Reservation"
    
    order_id = fields.Many2one('pos.order','POS Order')
    