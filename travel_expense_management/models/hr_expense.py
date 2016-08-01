# -*- coding: utf-8 -*-
from openerp import api, fields, models, _, tools
import dateutil

def _compute_amount(tax_id, base_amount, price_unit, quantity=1.0,
    product=None, partner=None):
    """ Returns the amount of a single tax. base_amount is the actual amount on which the tax is applied, which is
        price_unit * quantity eventually affected by previous taxes (if tax is include_base_amount XOR price_include)
    """
    if tax_id.amount_type == 'fixed':
        return math.copysign(self.amount, base_amount) * quantity

    if tax_id.amount_type == 'percent':
        return base_amount - (base_amount / (1 + tax_id.amount / 100))

    if tax_id.amount_type == 'division':
        return base_amount / (1 - tax_id.amount / 100) - base_amount

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

    unit_amount_untaxed = fields.Monetary(string = _("Amount Brutto"))

    @api.onchange('unit_amount_untaxed', 'tax_ids')
    def onchange_unit_amount_untaxed(self):
        amounts = 0.0
        company_id = self.env.user.company_id
        currency_id = company_id.currency_id

        for tax_id in self.tax_ids:
            prec = currency_id.decimal_places

            # CHECK AFTER UPDATE
            amount = _compute_amount(tax_id,
                self.unit_amount_untaxed, self.currency_id, 1,#quantity
                self.product_id, self.employee_id.user_id.partner_id)

            if (company_id.tax_calculation_rounding_method == 'round_globally'
                or not bool(self.env.context.get("round", True))):
                prec += 5

                amounts += round(amount, prec)
            else:
                amounts += currency_id.round(amount)

        self.unit_amount = currency_id.round(
            self.unit_amount_untaxed - abs(amounts))

    @api.depends('image')
    def _compute_images(self):
        for rec in self:
            rec.image_medium = tools.image_resize_image_medium(
                rec.image, avoid_if_small=True)
            rec.image_small = tools.image_resize_image_small(rec.image)

    @api.model
    def create(self, vals):
        res_id = super(HrExpense, self).create(vals)

        if res_id.employee_id.expense_sequence_id:
            ref = res_id.employee_id.expense_sequence_id._next()
            res_id.ref = "{identification_id}/{journey_start_year}/{ref}".format(
                identification_id = str(res_id.employee_id.identification_id),
                journey_start_year = dateutil.parser.parse(
                    res_id.date).year,
                ref = ref
            )

        return res_id


class HrExpenseTravel(models.Model):
    _name = 'hr.expense.travel'

    ref = fields.Char(string = _("Reference"), readonly = True)

    company_id = fields.Many2one('res.company', string='Company',
        readonly=True, # states={'draft': [('readonly', False)]},
        default=lambda self: self.env.user.company_id)

    employee_id = fields.Many2one('hr.employee', string=_("Employee"),
        required=True,
        default=lambda self: self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
    )
    employee_name = fields.Char(related = 'employee_id.name')

    travel_type = fields.Selection(string = _("Travel type"), selection = [
        ('domestic', _("Domestic")),
        ('international', _("International")),
    ])

    journey_start = fields.Datetime(string = _("Journey start"),
        compute = 'compute_line_information', readonly = True, required = True)
    journey_end = fields.Datetime(string = _("Journey end"),
        compute = 'compute_line_information', readonly = True, required = True)

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

    @api.multi
    def action_expense_documents(self):
        self.ensure_one()

        expense_ids = self.expense_ids.mapped('id')

        res = self.env['ir.actions.act_window'].for_xml_id(
            'base', 'action_attachment')

        res['domain'] = [
            ('res_model', '=', 'hr.expense'),
            ('res_id', 'in', expense_ids)
        ]
        res['context'] = {
            'default_res_model': 'hr.expense'
        }
        return res

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

    @api.onchange('event')
    def onchange_event(self):
        if self.event in ('journey_start', 'journey_end'):
            self.location = (
                self.travel_id.employee_id.work_location)
            self.travel_country_id = (
                self.travel_id.employee_id.company_id.country_id.id)
        elif self.event == 'domestic_return':
            self.travel_country_id = (
                self.travel_id.employee_id.company_id.country_id.id)
        elif self.travel_id.travel_type == 'domestic':
            self.travel_country_id = (
                self.travel_id.employee_id.company_id.country_id.id)

class HrExpenseTravelDeductions(models.Model):
    _name = 'hr.expense.travel.deduction'
    _order = 'date'

    travel_id = fields.Many2one(comodel_name = 'hr.expense.travel')

    date = fields.Date(string = _("Date"))
    location = fields.Char(string = _("Location"))
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
    location = fields.Char(string = _("Location"))
    name = fields.Char(string = _("Name"))
    date = fields.Date(string = _("Date"))
