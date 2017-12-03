from odoo import api, fields, models, _

class ResUsers(models.Model):
    _inherit = "res.users"
    _description = "WholeSale POS Res Users"
    
    @api.model
    def customize_has_groups(self, groups_ext_ids):
        """here groups_ext_ids is a list of groups(external_id may be)"""
        if not groups_ext_ids:
            return False
        user = self.env.user
        user_group_list = [i.id for i in user.groups_id]
        for group in groups_ext_ids:
            group_id = self.env.ref(group).id
            if group_id in user_group_list:
                return True
        return False
    