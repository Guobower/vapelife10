from odoo import api, fields, models, _

class ResCompany(models.Model):
    _inherit = "res.company"

    paid_image = fields.Binary("Paid Stamp")
    ship_image = fields.Binary("Free Shipping Stamp")
