from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = "product.template"
    _description = "Vapelife Product template"
    
    
    @api.depends('product_variant_ids', 'product_variant_ids.standard_price')
    def _compute_standard_price(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.standard_price = template.product_variant_ids.standard_price
        for template in (self - unique_variants):
            template.standard_price = 0.0

    @api.one
    def _set_standard_price(self):
        self.product_variant_ids.write({'standard_price':self.standard_price})    