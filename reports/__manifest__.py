# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Vape Reports',
    'version': '1.0',
    'category': 'jginfosystems',
    'sequence': 15,
    'summary': 'Reports',
    'description': """
    
A seprate tab is created for displaying reports in one place.Follwing Reports have been added:

* Treasury Analysis
* Invoice Analysis
* POS Order Analysis

""",
    'website': 'https://www.odoo.com/page/crm',
    'depends': ['base','point_of_sale'],
    'data': [
        'views/reports.xml',
        'views/account_treasury_report_view.xml',
    ],
    'demo': [
    ],
    'qweb': [],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
