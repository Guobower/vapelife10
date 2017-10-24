from odoo import api, fields, models, _
from odoo.exceptions import  ValidationError

_ACCOUNT_TYPE = [('website',"Website"),('wholesale','Wholesale/Distributer'),('vapeshop','Vapeshop'),('other','Others')]
_NATURE = [('vol',"Volume"),('conc','Concentration'),('flav','Flavor'),('none','None')]


class ProductAttribute(models.Model):
    _inherit = "product.attribute"
    _description = "Vapelife"

    @api.constrains('nature')
    def _validate_nature(self):
        vol_count = self.search_count([('nature','=','vol')])
        conc_count = self.search_count([('nature','=','conc')])
        flav_count = self.search_count([('nature','=','flav')])
        if vol_count > 1:
            raise ValidationError("Volume can only be assigned to single attribute")

        if conc_count > 1:
            raise ValidationError("Concentration can only be assigned to single attribute")

        if flav_count > 1:
            raise ValidationError("Flavor can only be assigned to single attribute")


    nature = fields.Selection(_NATURE,string = "Nature",required=True,default="none")

class ProductAttributeValue(models.Model):
    _inherit  = "product.attribute.value"
    _description = "Vapelife"

    actual_value = fields.Float('Actual Value')