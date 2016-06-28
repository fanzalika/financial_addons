# -*- coding: utf-8 -*-
from openerp import api, fields, models, _, exceptions

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    for_expense = fields.Boolean(string = _("for Expense"))
    expense_arrival = fields.Datetime(string = _("Expense arrival"))
    expense_arrival_country = fields.Many2one(string = _("Expense country"),
        comodel_name = 'res.country')
    expense_travel_id = fields.Many2one('hr.expense.travel',
        string = _("Travel Expense"))

    @api.multi
    def write(self, vals, context = None):
        res_id = super(CalendarEvent, self).write(vals, context)

        #line_start_id = self.env['hr.expense.travel.line'].create({
        #    'event': 'journey_start',
        #    'date': res_id.start_datetime
        #})

        #line_start_id = self.env['hr.expense.travel.line'].create({
        #    'event': 'journey_start',
        #    'date': res_id.start_datetime
        #})

        if res_id.for_expense and not self.expense_travel_id:
            self.expense_travel_id = self.env["hr.expense.travel"].create({
                'name': res_id.name,
                'line_ids': [
                    (0, False, {
                        'event': 'journey_start',
                        'date': res_id.start_datetime
                    }),
                    (0, False, {
                        'event': 'travel_dest_arrival',
                        'travel_country_id': res_id.expense_arrival_country
                    })
                    (0, False, {
                        'event': 'journey_end',
                        'date': res_id.stop_datetime
                    })
                ]
            })

        return res_id
