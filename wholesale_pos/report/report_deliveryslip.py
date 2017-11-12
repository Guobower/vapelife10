from odoo import api, models

class DeliverySlipTabular(models.AbstractModel):
    _name = 'report.wholesale_pos.report_deliveryslip_tabular'
    
    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('wholesale_pos.report_deliveryslip_tabular')
        data = self.env['stock.picking'].search([('id','in',docids)]).get_print_tabular_data()
        print data
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs':self.env[report.model].browse(docids),
            'data':data
        }
        return report_obj.render('wholesale_pos.report_deliveryslip_tabular', docargs)