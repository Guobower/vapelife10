# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'POS Orders',
    'version': '1.0',
    'category': 'jginfosystems',
    'sequence': 15,
    'summary': 'Search and Print Orders in POS',
    'description': """
        This module provides a screen to display and print POS orders in the POS 
    """,
    'website': 'https://www.odoo.com',
    'depends': ['base','point_of_sale'],
    'data': [
        'views/pos_order.xml',
        'data/report_paperformat.xml',
        'report/receipt_report.xml',
        'views/report.xml'
    ],
    'demo': [
    ],
    'css': [],
    'images': [],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
