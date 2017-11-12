# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'WholeSale POS',
    'version': '1.0',
    'category': 'vapelife',
    'sequence': 15,
    'summary': 'Wholesale inside POS',
    'description': """

    """,
    'website': 'https://www.odoo.com/page/crm',
    'depends': ['base','product','sales_team','vapelife','account','point_of_sale','sale'],
    'data': [
        'views/product_tab_view.xml',
        'views/wholesale_pos.xml',
        'views/ir_sequence_data.xml',
        'views/payment_plan_view.xml',
        'views/account_invoice_view.xml',
        'views/account_payment_view.xml',
        'views/stock_report_views.xml',
        'report/report_deliveryslip.xml',
        'views/stock_picking_view.xml',
        'views/res_company.xml'
    ],
    'demo': [
    ],
    'css': [],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
