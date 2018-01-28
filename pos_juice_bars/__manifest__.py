# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Juice Bars Mixture',
    'version': '1.0',
    'category': 'jginfosystems',
    'sequence': 15,
    'summary': 'Juice Bars Mixture',
    'description': """
Configuration
-------------
* Create BOMs with for all the Jucie Bars
* Set the manufacturing picking type for all the Point of Sales

Functionality
-------------
This module attaches a wizard to all the products that are selected in the point of sales settings for Juice Bars. 
Following are fields to be setup in the Point of Sale Settings

* *Juice Bar Volume*: Only products having this volume attribute will be displayed for mixture in the wizard
* *Juice Bars*: Prduct which on click in POS will trigger the wizard and be manufactured by the chosen mixture in the wizard
* *Juice Bar Mixture Concentrations*: Juice havin these concentration will be displayed seperately tab wise of the above volume option selected.

""",
    'website': 'https://www.odoo.com/page/crm',
    'depends': ['base','point_of_sale','vapelife','mrp'],
    'data': [
        'views/res_config_view.xml',
        'views/pos_juice_bars.xml',
        'views/point_of_sale_view.xml',
        'security/ir.model.access.csv',
        'views/pos_config_view.xml'
    ],
    'demo': [
    ],
    'qweb': ['static/src/xml/*.xml'],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
