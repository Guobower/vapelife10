# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Point of Sale Extended',
    'version': '1.0',
    'category': 'jginfosystems',
    'sequence': 15,
    'summary': 'Point of Sale Extension',
    'description': """
        * Changed Payment Numpad Template in Point Of Sale 
    """,
    'website': 'https://www.odoo.com',
    'depends': ['base','point_of_sale'],
    'data': [
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
