# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Vapelife Frachise User',
    'version': '1.0',
    'category': 'jginfosystems',
    'sequence': 15,
    'summary': 'Vapelife Frachise User',
    'description': """
    
    * Added views for the franchise users

""",
    'website': 'https://www.odoo.com/page/crm',
    'depends': ['base','point_of_sale'],
    'data': [
        'views/pos_config.xml',
        'views/pos_franchise.xml',
        'security/pos_franchise_security.xml',
        'security/ir.model.access.csv',        
    ],
    'demo': [
    ],
    'qweb': ['static/src/xml/*.xml'],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
