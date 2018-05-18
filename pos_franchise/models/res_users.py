from openerp import models, fields, api, _,SUPERUSER_ID

class ResUsers(models.Model):
    _inherit = "res.users"

    parent_id = fields.Many2one('res.users','Manager',index=True)
    parent_name = fields.Char(related='parent_id.name', readonly=True, string='Parent name')
    child_ids = fields.One2many('res.users','parent_id','POS Users')
    pos_ids = fields.One2many('pos.config','default_user_id','Responsible For')
    
    
    