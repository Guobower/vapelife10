from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = "product.template"
    _description = "Vapelife Product Template"

    @api.multi
    def write(self,vals):
        return super(ProductTemplate,self).write(vals)


    # tab_id = fields.Many2one("product.tab",string = "Product Tab")