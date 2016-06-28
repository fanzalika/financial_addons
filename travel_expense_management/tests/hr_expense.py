from openerp.tests.common import TransactionCase

class TravelManagementTestCase(TransactionCase):
    post_install = True
    at_install = False

    def setUp(self):
        super(TravelManagementTestCase, self).setUp()

        self.hr_expense_travel = self.env['hr.expense.travel']
        self.hr_expense_travel_line = self.env['hr.expense.travel.line']
        self.hr_expense_travel_deductions = self.env[
            'hr.expense.travel.deductions']
        self.hr_expense = self.env['hr.expense']

    def test_base(self):
        line1 = self.hr_expense_travel_line.create({
            'event': 'journey_start',
            'date': "2016-06-26 16:00:00",
            'travel_country_id': self.env.ref('base.de').id,
            'location': 'Heidelberg'
        })
        line2 = self.hr_expense_travel_line.create({
            'event': 'journey_start',
            'date': "2016-06-26 22:00:00",
            'travel_country_id': self.env.ref('base.de').id,
            'location': 'Hamburg'
        })
        line3 = self.hr_expense_travel_line.create({
            'event': 'journey_start',
            'date': "2016-07-01 15:00:00",
            'travel_country_id': self.env.ref('base.de').id,
            'location': 'Hamburg'
        })
        line4 = self.hr_expense_travel_line.create({
            'event': 'journey_start',
            'date': "2016-07-01 21:00:00",
            'travel_country_id': self.env.ref('base.de').id,
            'location': 'Heidelberg'
        })
        print "TEST"

# -
#   In order to test Travel Expense Management I create a travel expense and
#   confirm it
# -
#   I write down the different steps of the journey
# -
#   !record {model: hr.expense.travel, id: travel_management0}: |
#     name: 'Test'
#     line_ids:
#       - event: 'journey_start'
#         date: '2016-06-26 16:00:00'
#         travel_country_id: base.de
#         location: 'Heidelberg'
#       - event: 'travel_dest_arrival'
#         date: '2016-06-26 22:00:00'
#         travel_country_id: base.de
#         location: 'Hamburg'
#       - event: 'journey_dest_departure'
#         date: '2016-07-01 15:00:00'
#         travel_country_id: base.de
#         location: 'Hamburg'
#       - event: 'journey_end'
#         date: '2016-07-01 21:00:00'
#         travel_country_id: base.de
#         location: 'Heidelberg'
# -
#   next step
# -
#   !assert {model: account.invoice, id: account_invoice_state}:
#     - False
