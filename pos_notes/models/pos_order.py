from openerp import models, fields, api, _

class PosOrder(models.Model):

    _inherit = "pos.order"
    _description = "POS Order Vapelife"

    @api.model
    def _order_fields(self, ui_order):
        vals = super(PosOrder,self)._order_fields(ui_order)
        vals.update({
            'note':ui_order['note'] or '',
        })
        return vals

    @api.model
    def create_from_ui(self, orders):
        return super(PosOrder,self).create_from_ui(orders)