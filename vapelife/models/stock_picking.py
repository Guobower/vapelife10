from odoo import api, fields, models, _

class StockPicking(models.Model):
    _inherit = "stock.picking"
    _description = "Stock Picking Vapelife"
    
    
    @api.one
    @api.depends('move_lines.procurement_id.sale_line_id.order_id')
    def _get_sale_note(self):
        if self.sale_id:
            self.sale_note  = self.sale_id.note
            return
    
    
    sale_note = fields.Text(string = "Sale Note",compute = "_get_sale_note")
    