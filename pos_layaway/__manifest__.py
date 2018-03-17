# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'POS Layaway',
    'version': '1.0',
    'category': 'vapelife',
    'sequence': 15,
    'summary': 'POS Layaway',
    'description': """

        This module is dependent of order_reprinting_pos. It is used to add layaway functionality to POS

    """,
    'website': 'https://www.odoo.com',
    'depends': ['base','point_of_sale','stock_reserve','pos_order'],
    'data': [
        'views/pos_layaway.xml',
        'views/pos_order_view.xml',
        'report/receipt_report.xml',
        'data/report_paperformat.xml',
        'views/point_of_sale_report.xml',
    ],
    'demo': [
    ],
    'css': [],
    'images': ['static/description/banner.jpg'],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
