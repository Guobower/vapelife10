from odoo import api, fields, models, _
from pyPdf import PdfFileWriter, PdfFileReader

class PosSession(models.Model):
    _inherit = "pos.session"
    _description = "WholeSale POS sessions"

    def _get_order_lines(self,line,discount_percentage):
        line.update({
                'discount':discount_percentage,
            })
        return [0,0,line]
    
    @api.model
    def confirm_order_interface(self,order):
        lines = map(lambda line: self._get_order_lines(line,order['discount_percentage']),order['order_lines'])
        if order['shipping_handling'] > 0:
            s_h_product_id = self.env['ir.values'].sudo().get_default('sale.config.settings', 'shipping_product_id')
            if s_h_product_id:
                lines.append([0,0,{
                        'product_id':s_h_product_id,
                        'price_unit':order['shipping_handling'],
                        'product_uom_qty':1
                    }])
        sale_order = self.env['sale.order'].create({
                'partner_id':order['partner_id'],
                'note':order['note'],
                'order_line':lines,
            })
        sale_order.action_confirm()
        wizard_id = self.env['sale.advance.payment.inv'].create({'advance_payment_method':'all'})
        res = wizard_id.with_context(open_invoices = True,active_ids = sale_order.id).create_invoices()
        account_invoice = self.env['account.invoice'].search([('id','=',res.get('res_id',False))],limit=1)
        account_invoice.with_context(type = 'out_invoice', journal_type =  'sale').action_invoice_open()
        journal = self.env['account.journal'].browse(int(order['payment_method']))
        if order['paid'] > 0:
            account_payment_defaults = self.env['account.payment'].with_context(default_invoice_ids = [(4,account_invoice.id,None)]).default_get([
                'communication', 'invoice_ids', 'payment_difference', 'partner_id', 'payment_method_id', 'payment_date', 'display_name', '__last_update', 
                 'payment_difference_handling', 'company_id', 'state', 'writeoff_account_id', 'move_name', 'has_invoices', 'payment_method_code', 'move_line_ids',
                 'payment_transaction_id', 'payment_token_id', 'name', 'hide_payment_method', 'partner_type', 'destination_journal_id', 'payment_type', 
                 'payment_reference', 'destination_account_id'
                 ])            
            payment_methods = account_payment_defaults['payment_type'] == 'inbound' and journal.inbound_payment_method_ids or journal.outbound_payment_method_ids
            account_payment = self.env['account.payment'].with_context(default_invoice_ids = [(4,account_invoice.id,None)]
                                                                       ).create({
                                                                            'journal_id':int(order['payment_method']),
                                                                            'amount':order['paid'],
                                                                            'payment_method_id': payment_methods and payment_methods[0].id or False,
                                                                        })
            account_payment.post()
        invoice_report = self.env['report'].get_action(account_invoice, 'account.report_invoice')
        if order['payment_lines']:
            account_invoice.write({'payment_plan_ids':[[0,0,line] for line in order['payment_lines']]})
            
        return invoice_report