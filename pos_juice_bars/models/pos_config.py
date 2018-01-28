from openerp import models, fields, api, _
from odoo.tools import float_is_zero

class PosConfig(models.Model):
    _inherit = "pos.config"
    
    manufacturing_picking_type_id = fields.Many2one('stock.picking.type','Manufacturing Picking Type',domain=[('code','=','mrp_operation')])