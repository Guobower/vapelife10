from odoo import api, fields, models

class SaleConfiguration(models.TransientModel):
    _inherit = 'sale.config.settings'

    @api.one
    def set_default_shipping_product_id(self):
        return self.env['ir.values'].sudo().set_default(
            'sale.config.settings', 'shipping_product_id', self.shipping_product_id.id)

    @api.one
    def get_default_shipping_product_id(self,fields):
        return self.env['ir.values'].sudo().get_default(
            'sale.config.settings', 'shipping_product_id') or []

    shipping_product_id = fields.Many2one(
        'product.product',
        'Shipping Product',
        domain="[('type', '=', 'service')]",
        help='Default product used for payment advances')


