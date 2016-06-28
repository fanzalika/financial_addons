# -*- coding: utf-8 -*-
from openerp import api, fields, models, _, tools
import dateutil

class HrExpense(models.Model):
    _inherit = 'hr.expense'
    _name = 'hr.expense'

    ref = fields.Char(string = _("Reference"), readonly = True)
    expense_type = fields.Selection(string = _("Expense type"),
        selection = [
            ('travel', _("Travel")),
            ('refreshment', _("Refreshment")),
            ('others', _("Others")),
        ])
    expense_id = fields.Many2one(string = _("Travel Expense"),
        comodel_name = 'hr.expense.travel')
    expense_location = fields.Char(string = _("Expense location"))
    expense_country = fields.Many2one(string = _("Expense country"),
        comodel_name = 'res.country')
    expense_restaurant = fields.Char(string = _("Restaurant"))
    number_attendees = fields.Integer(string = _("Number of attendees"))
    attendees_internal = fields.Many2many(string = _("Internal attendees"),
        comodel_name = 'res.users')
    attendees_partner = fields.Many2many(string = _("Attendees partner"),
        comodel_name = 'res.partner')
    attendees_other = fields.Char(string = _("other attendees"))
    waiter_tip = fields.Boolean(string = _("Waiter tip"))
    waiter_tip_amount = fields.Float(string = _("Waiter tip amount"))

    image = fields.Binary(string=_('Image'), attachement=True)
    image_medium = fields.Binary(
        string=_('Image'), attachement=True, compute='_compute_images',
        inverse='_inverse_image_medium', store=True)
    image_small = fields.Binary(
        string=_('Image'), attachement=True, compute='_compute_images',
        inverse='_inverse_image_small', store=True)

    @api.depends('image')
    def _compute_images(self):
        for rec in self:
            rec.image_medium = tools.image_resize_image_medium(
                rec.image, avoid_if_small=True)
            rec.image_small = tools.image_resize_image_small(rec.image)

    @api.model
    def create(self, vals):
        res_id = super(HrExpenseTravel, self).create(vals)
        res_id.ref = sequence_obj._next()
        return super(HrExpense, self).create(vals)


class HrExpenseTravel(models.Model):
    _name = 'hr.expense.travel'

    ref = fields.Char(string = _("Reference"), readonly = True)

    employee_id = fields.Many2one('hr.employee', string=_("Employee"),
        required=True,
        default=lambda self: self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
    )
    employee_name = fields.Char(related = 'employee_id.name')
    name = fields.Char(string = _("Name"), required = True)

    journey_start = fields.Datetime(string = _("Journey start"),
        compute = 'compute_line_information', readonly = True, required = True)
    journey_end = fields.Datetime(string = _("Journey end"),
        compute = 'compute_line_information', readonly = True, required = True)
    travel_country_id = fields.Many2one('res.country', required = True,
        readonly = True, string = _("First Destination Country"),
        compute = 'compute_line_information')

    reason = fields.Text(string = _("Reason"),
        compute = 'compute_line_information', readonly = True)

    line_ids = fields.One2many(string = _("Schedule"),
        comodel_name = 'hr.expense.travel.line', inverse_name = 'travel_id')

    reason_ids = fields.One2many('hr.expense.travel.reason',
        inverse_name = 'travel_id')

    distance_km = fields.Float(string = _("Distance (km)"))

    subsistence_lump_sum = fields.Boolean(string = _("Subsistence lump sum"))
    accomodation_lump_sum = fields.Boolean(string = _("Accomodation lump sum"))

    deduction_ids = fields.One2many('hr.expense.travel.deduction',
        string = _("Deductions"), inverse_name = 'travel_id')

    expense_ids = fields.Many2many(string=_('Expenses'),
        comodel_name='hr.expense', inverse_name = 'expense_id', domain=[
            ('expense_id', '=', False)
        ])

    @api.multi
    @api.depends('line_ids')
    def compute_line_information(self):
        for row in self:
            for line in row.line_ids:
                if line.event == "journey_start":
                    row.journey_start = line.date
                elif line.event == "travel_dest_arrival":
                    row.travel_country_id = line.travel_country_id
                elif line.event == "travel_dest_departure":
                    pass
                if line.event == "domestic_return":
                    pass
                if line.event == "journey_end":
                    row.journey_end = line.date

    @api.model
    def create(self, vals):
        res_id = super(HrExpenseTravel, self).create(vals)

        for line_id in res_id.line_ids:
            res_id.reason_ids.create({
                'date': line_id.date
            })

            res_id.deduction_ids.create({
                'date': line_id.date
            })

        if res_id.employee_id.expense_sequence_id:
            ref = res_id.employee_id.expense_sequence_id._next()
            res_id.ref = "{identification_id}/{journey_start_year}/{ref}".format(
                identification_id = str(res_id.employee_id.identification_id),
                journey_start_year = dateutil.parser.parse(
                    res_id.journey_start).year,
                ref = ref
            )

        return res_id

class HrExpenseTravelLine(models.Model):
    _name = 'hr.expense.travel.line'
    _rec_name = 'event'
    _order = 'date'

    travel_id = fields.Many2one(comodel_name = 'hr.expense.travel')

    event = fields.Selection(string = _("Event"), selection = [
        ('journey_start', _('Journey start')),
        ('travel_dest_arrival', _('Travel destination arrival')),
        ('travel_dest_departure', _('Travel destination departure')),
        ('domestic_return', _('Domestic return')),
        ('journey_end', _('Journey end')),
    ])

    date = fields.Datetime(string = _("Date"))
    location = fields.Char(string = _("Location"))
    travel_country_id = fields.Many2one('res.country', string = _("Country"))

    type = fields.Selection(string = _("Type"), selection = [
        ('business', "Business trip"),
        ('private', "Private trip"),
    ])

class HrExpenseTravelDeductions(models.Model):
    _name = 'hr.expense.travel.deduction'
    _order = 'date'

    travel_id = fields.Many2one(comodel_name = 'hr.expense.travel')

    date = fields.Date(string = _("Date"))
    weekday = fields.Char(string = _("Weekday"), compute = 'compute_weekday',
        readonly = True)
    breakfast = fields.Boolean(string = _("Breakfast"))
    lunch = fields.Boolean(string = _("Lunch"))
    dinner = fields.Boolean(string = _("Dinner"))
    nightmeal = fields.Boolean(string = _("Nightmeal"))

    @api.multi
    @api.depends('date')
    def compute_weekday(self):
        for row in self:
            try:
                row.weekday = dateutil.parser.parse(row.date).strftime("%A")
            except AttributeError:
                pass

class HrExpenseTravelReason(models.Model):
    _name = 'hr.expense.travel.reason'
    _rec_name = 'reason'
    _order = 'date'

    travel_id = fields.Many2one(comodel_name = 'hr.expense.travel')
    reason = fields.Char(string = _("Reason"))
    name = fields.Char(string = _("Name"))
    date = fields.Date(string = _("Date"))
