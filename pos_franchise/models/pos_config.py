from openerp import models, fields, api, _

class PosConfig(models.Model):
    _inherit = "pos.config"
    _description = "POS Franchise"
    default_user_id = fields.Many2one('res.users','Default User')