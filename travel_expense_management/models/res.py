# -*- coding: utf-8 -*-
from openerp import api, fields, models, _


class TravelManagementConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'travel_management.config.settings'

    lumprate = fields.Float(
        string=_('Lump rate'))

    @api.model
    def get_default_values(self, fields):
        return {
            'lumprate': 30.0
        }

    @api.one
    def set_values(self):
        self.env['ir.values'].set_default(
            'travel_management.config.settings', 'lumprate',
			self.lumprate)
