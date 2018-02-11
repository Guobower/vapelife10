# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


import odoo.addons.decimal_precision as dp
from odoo import tools
from odoo import models, fields, api


class account_treasury_report(models.Model):
    _name = "account.treasury.report"
    _description = "Treasury Analysis"
    _auto = False
    _rec_name = 'account_id'

    @api.multi
    def _compute_balances(self):
        all_companies = self.env['res.company'].search([])
        current_sum = dict((company.id, 0.0) for company in all_companies)
        for record in self:
            record.starting_balance = current_sum[record.company_id.id] 
            current_sum[record.company_id.id] += record.balance
            record.ending_balance = current_sum[record.company_id.id]
    
    account_id = fields.Many2one('account.account',string="Account",readonly=True)
    partner_id = fields.Many2one('res.partner',string="Partner",readonly=True)
    debit =  fields.Float('Debit', readonly=True)
    credit = fields.Float('Credit', readonly=True)
    balance =  fields.Float('Balance', readonly=True)
    date =  fields.Date('Date', readonly=True)
    starting_balance = fields.Float(compute = "_compute_balances", digits=dp.get_precision('Account'), string='Starting Balance')
    ending_balance =  fields.Float(compute = "_compute_balances", digits=dp.get_precision('Account'), string='Ending Balance')
    company_id =  fields.Many2one('res.company', 'Company', readonly=True)
    _order = 'date asc'

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            create or replace view account_treasury_report as (
            select
                a.id as id,
                a.id as account_id,
                l.partner_id as partner_id,
                sum(l.debit) as debit,
                sum(l.credit) as credit,
                sum(l.debit-l.credit) as balance,
                am.date as date,
                am.company_id as company_id
            from
                account_move_line l
                left join account_account a on (l.account_id = a.id)
                left join account_move am on (am.id=l.move_id)
                left join account_account_type aat on (aat.id = a.user_type_id) 
            where am.state != 'draft' and aat.type = 'liquidity'
            group by a.id,am.company_id,am.date,l.partner_id
            )
        """)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
