# -*- coding: utf-8 -*-
from openerp import api, fields, models, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    expense_sequence_id = fields.Many2one(
        string = _("Expense reference sequence"), comodel_name = 'ir.sequence')
