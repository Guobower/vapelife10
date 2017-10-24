from odoo import api, fields, models, _, exceptions

PARAMS = [
    ("juicebar_volume_id", "pos_juice_bars.juicebar_volume_id"),
]

class PosConfig(models.TransientModel):

    _inherit = "pos.config.settings"
    _description = "Vapelife Juice Bars Config"

    @api.one
    def set_default_juicebar_volume_id(self):
        params = self.env['ir.config_parameter']
        params.set_param('pos_juice_bars.juicebar_volume_id', (self.juicebar_volume_id.id))

    @api.model
    def get_default_juicebar_volume_id(self,fields):
        params = self.env['ir.config_parameter']
        return {
            'juicebar_volume_id': int(params.get_param('pos_juice_bars.juicebar_volume_id'))
        }

    def _get_domain_concentration(self,context=None):
        # We have access to self.env in this context.
        ids = self.env.ref('vapelife.nicotine_attribute').id
        return [('attribute_id','=', ids)]

    @api.one
    def set_default_juicebar_concentration_ids(self):
        params = self.env['ir.config_parameter']
        juicebar_concentration_ids = map(lambda x: x.id, self.juicebar_concentration_ids)
        params.set_param('pos_juice_bars.juicebar_concentration_ids', (juicebar_concentration_ids))

    @api.model
    def get_default_attributes_available_ids(self,fields):
        params = self.env['ir.config_parameter']
        try:
            juicebar_concentration_ids = params.get_param('pos_juice_bars.juicebar_concentration_ids', default='[]')
            return dict(juicebar_concentration_ids=[(6, 0, eval(juicebar_concentration_ids))])
        except Exception as e:
            raise exceptions.except_orm('Error','Invalid Concentration Records IDs')

    @api.one
    def set_default_juice_bars_ids(self):
        params = self.env['ir.config_parameter']
        juice_bars_ids = map(lambda x: x.id, self.juice_bars_ids)
        params.set_param('pos_juice_bars.juice_bars_ids', (juice_bars_ids))

    @api.model
    def get_default_juice_bars_ids(self, fields):
        params = self.env['ir.config_parameter']
        try:
            juice_bars_ids = params.get_param('pos_juice_bars.juice_bars_ids', default='[]')
            return dict(juice_bars_ids=[(6, 0, eval(juice_bars_ids))])
        except Exception as e:
            raise exceptions.except_orm('Error', 'Invalid Juice Bar IDs')

    # @api.one
    # def set_params(self):
    #     self.ensure_one()
    #
    #     for field_name, key_name in PARAMS:
    #         value = getattr(self, field_name, '').strip()
    #         self.env['ir.config_parameter'].set_param(key_name, value)
    #
    # @api.one
    # def get_default_params(self, fields):
    #     res = {}
    #     for field_name, key_name in PARAMS:
    #         res[field_name] = self.env['ir.config_parameter'].get_param(key_name, '').strip()
    #     return res


    juicebar_volume_id = fields.Many2one('product.attribute.value',string = "Juice Bar Volume")
    juicebar_concentration_ids = fields.Many2many('product.attribute.value','vapelife_config_product_attribute_value',
                                                  column1 = "pos_config_id",column2="attribute_value_id",string = "Juice Bar Mixture Concentrations",
                                                  domain = _get_domain_concentration
                                                  )
    juice_bars_ids = fields.Many2many('product.product','pos_config_settings_product_product',column1 = "pos_config_id",column2="product_id",
                                      string = "Juice Bars"
                                      )