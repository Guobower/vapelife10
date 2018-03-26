# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'POS Product Return',
    'version': '1.0',
    'category': 'jginfosystems',
    'sequence': 15,
    'summary': 'POS Product Return',
    'description': """
        This module provides easy interface to return products from POS
    """,
    'website': 'https://www.odoo.com',
    'depends': ['base','point_of_sale','pos_order'],
    'data': [
        'views/point_of_sale_return.xml',
        'views/pos_order_view.xml'
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
