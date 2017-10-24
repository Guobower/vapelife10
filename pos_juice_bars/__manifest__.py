# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Vapelife Juice Bars Mixture',
    'version': '1.0',
    'category': 'vapelife',
    'sequence': 15,
    'summary': 'Vapelife Juice Bars Mixture',
    'description': """
    This module adds a mixture wizard for 350ml Juices

    """,
    'website': 'https://www.odoo.com/page/crm',
    'depends': ['base','point_of_sale','vapelife'],
    'data': [
        'views/res_config_view.xml',
        'views/pos_juice_bars.xml',
        'views/point_of_sale_view.xml',
    ],
    'demo': [
    ],
    'qweb': ['static/src/xml/*.xml'],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
