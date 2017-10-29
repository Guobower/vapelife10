# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Vapelife Main',
    'version': '1.0',
    'category': 'vapelife',
    'sequence': 15,
    'summary': 'Vapelife Backend Module',
    'description': """
* Added Leads field and filter and created seperate menu item for it
* Added two fields in Partner. Tax ID and type of account
* Added Actual Value field to Product Attribute Value
* Added product attribute and product attribute value field to product category
    """,
    'website': 'https://www.odoo.com/page/crm',
    'depends': ['base','sales_team','sale','product'],
    'data': [
        'views/res_partner.xml',
        'views/product_attribute_views.xml',
        'data/product_attribute_data.xml',
        'views/product.xml',
        'views/sale_config_settings_views.xml',
        'views/account_invoice_view.xml'
    ],
    'demo': [
    ],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
