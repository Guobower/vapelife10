from odoo import api, fields, models, _

_ACCOUNT_TYPE = [('website',"Website"),('wholesale','Wholesale/Distributer'),('vapeshop','Vapeshop'),('other','Others')]

class ResPartner(models.Model):
    _inherit = "res.partner"
    _description = "Vapelife Partner"

    account_type = fields.Selection(_ACCOUNT_TYPE,string="Type of Account",default="other")
    tax_id = fields.Char(string = "Tax ID")
    leads = fields.Boolean('Is a Lead')
