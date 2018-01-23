# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Purchase Extended',
    'version': '1.0',
    'category': 'jginfosystems',
    'sequence': 15,
    'summary': 'Purchase Extended',
    'description': """

        1. When we create and confirm the PO an Invoice is created Automatically

    """,
    'website': 'https://www.odoo.com',
    'depends': ['base','purchase','account'],
    'data': [
        'views/purchase_views.xml'
    ],
    'demo': [
    ],
    'css': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
