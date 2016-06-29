# -*- coding: utf-8 -*-
{
    'name': "HLO Travel Management",

    'summary': "Modifications",

    'description': """
        A set of small modifications done to the Expense App.
    """,

    'author': "HLO",
    'website': "http://www.humanilog.org",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Expense',
    'version': '0.0.1',

    'depends': ['hr_expense', 'product', 'calendar'],

    'data': [
      'views/hr_expense.xml',
      'views/product.xml',
      'views/hr.xml',
      #'views/calendar.xml',
      'data/sequence.xml',
      'security/ir_rule.xml',
      'security/ir.model.access.csv'
    ]
}
