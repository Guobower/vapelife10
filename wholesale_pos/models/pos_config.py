from odoo import api, fields, models, tools, _

class PosConfig(models.Model):
    _inherit = "pos.config"
    _description = "Point of Sale Config Vapelife"

    warehouse_id = fields.Many2one('stock.warehouse','Warehouse')