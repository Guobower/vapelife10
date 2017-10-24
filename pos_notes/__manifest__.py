# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'POS Notes',
    'version': '1.0',
    'category': 'vapelife',
    'sequence': 15,
    'summary': 'POS Notes',
    'description': """

        This module allows user to add notes in POS. These notes are printed on the reciept as well as they are saved in the order at the backend

    """,
    'website': 'https://www.odoo.com/page/crm',
    'depends': ['base','point_of_sale'],
    'data': [
            'views/pos_notes.xml',
            'views/pos_order_view.xml',
    ],
    'demo': [
    ],
    'css': [],
    'qweb': ['static/src/xml/pos.xml'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
