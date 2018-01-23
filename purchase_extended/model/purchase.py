from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _description = "Purchase Order Extended"
    
    @api.multi
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step'\
                    or (order.company_id.po_double_validation == 'two_step'\
                        and order.amount_total < self.env.user.company_id.currency_id.compute(order.company_id.po_double_validation_amount, order.currency_id))\
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
                if self.create_vendor_bill:
                    # Create Purchase Invoice if ticked
                    invoice_object = self.env['account.invoice']
                    invoice_lines = []
                    invoice_id = invoice_object.create({'partner_id':self.partner_id.id,'reference':order.name,'date_invoice':fields.datetime.now()})
                    for line in self.order_line:
                        data = invoice_object._prepare_invoice_line_from_po_line(line)
                        invoice_lines.append((0,False,data))
                    invoice_id.write({'invoice_line_ids':invoice_lines})
            else:
                order.write({'state': 'to approve'})
        return True
    
    create_vendor_bill = fields.Boolean('Create Vendor Bill',default=True)