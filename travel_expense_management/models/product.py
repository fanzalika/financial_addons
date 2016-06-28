# -*- coding: utf-8 -*-
from openerp import api, fields, models, _

class ProductProduct(models.Model):
    _inherit = 'product.template'

    expense_type = fields.Selection(string = _("Expense type"),
        selection = [
            ('travel', _("Travel")),
            ('refreshment', _("Refreshment")),
            ('others', _("Others")),
        ])
