from openerp import models, fields, api, _

class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    _description = "WholeSale POS"
    
    payment_plan_ids  = fields.One2many('payment.plan','invoice_id','Payment Plans')
    