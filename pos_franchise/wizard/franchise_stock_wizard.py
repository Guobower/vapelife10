# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


class FranchiseStockWizardUser(models.TransientModel):
    _name = "franchise.stock.wizard.user"
    _description = "Franchise User Stock Wizard"
    
    @api.multi
    def display_stock(self):
        location_ids = []
        if self.env.user.has_group('pos_franchise.group_pos_franchise_manager'):
            location_ids = self.location_manager_ids.id
        else:
            location_ids = self.location_user_ids.id

        if not location_ids:
            raise UserError(_('Choose atleast one location.'))
        return {
            'name':_('Stock'),
            'view_type':'form',
            'view_mode':'tree',
            'res_model': 'stock.quant',
            'target': 'current',
            'domain':[('location_id', 'child_of', location_ids)],
            'type': 'ir.actions.act_window',
            'context':{'search_default_productgroup': 1,'search_default_locationgroup':1}
        }
    location_user_ids = fields.Many2many('stock.location',groups = "pos_franchise.group_pos_franchise_user",
                                         domain=lambda self: [('id','in',[self.env.user.pos_ids.stock_location_id.id])])
    
    location_manager_ids =  fields.Many2many('stock.location',groups = "pos_franchise.group_pos_franchise_manager",
                         domain=lambda self: ['|',('id','in',[self.env.user.child_ids.pos_ids.stock_location_id.id]),('id','in',[self.env.user.pos_ids.stock_location_id.id])])                          
                                   
    
