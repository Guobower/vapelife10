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
    'depends': ['base','point_of_sale','order_reprinting_pos'],
    'data': [
        'views/pos_layaway.xml'
    ],
    'demo': [
    ],
    'css': [],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
