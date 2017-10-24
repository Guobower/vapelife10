from openerp import models, fields, api, _

class AccountPayment(models.Model):
    _inherit = "account.payment"
    _description = "Wholesale POS"
    
    @api.multi
    def post(self):
        super(AccountPayment,self).post()
        if self.payment_plan_id:
            self.payment_plan_id.state = "paid"
        return
    
    @api.onchange('payment_plan_id')
    def _onchange_payment_plan_id(self):
        if self.payment_plan_id:
            self.amount = self.payment_plan_id.amount
            
    @api.onchange('invoice_ids')
    def _onchange_invoice_ids(self):
        # Set partner_id domain
        if self.invoice_ids:
            return {
                    'domain': {'payment_plan_id': [('invoice_id', 'in', [invoice.id for invoice in self.invoice_ids])]}
                    }
    
    
    payment_plan_id = fields.Many2one('payment.plan',string = "Payment Plan")