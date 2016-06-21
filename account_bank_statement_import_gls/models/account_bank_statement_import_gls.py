# -*- coding: utf-8 -*-

from openerp import api, fields, models, _, tools

import csv
import StringIO
from datetime import datetime
import operator
import codecs

HEADERS = [
    u'Kontonummer',
    u'Buchungstag',
    u'Wertstellung',
    u'Auftraggeber/Empfänger',
    u'Buchungstext',
    u'VWZ1',
    u'VWZ2',
    u'VWZ3',
    u'VWZ4',
    u'VWZ5',
    u'VWZ6',
    u'VWZ7',
    u'VWZ8',
    u'VWZ9',
    u'VWZ10',
    u'VWZ11',
    u'VWZ12',
    u'VWZ13',
    u'VWZ14',
    u'Betrag',
    u'Kontostand',
    u'Währung'
]

def iso8859_utf8(buf):
    return unicode(buf.decode("iso-8859-1").encode("utf8"), "utf8")

def iso8859_proxy(reader):
    #TODO: more performance by converting k only once
    for row in reader:
        ret = {iso8859_utf8(k): iso8859_utf8(v) for k, v in row.items()}
        yield ret

def monetize(s):
    r = s.replace(".", "").replace(",", ".")
    return float(r)

class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    @property
    def notifications(self):
        if getattr(self, "_notifications", None) is None:
            self._notifications = []
        return self._notifications

    def _parse_file(self, data_file):
        account_invoice = self.env["account.invoice"].search(
            [('reference', '!=', False)])

        try:
            reader = csv.DictReader(
                StringIO.StringIO(data_file), delimiter=";")
            fieldnames = map(
                lambda x: iso8859_utf8(x),
                reader.fieldnames
            )
            if fieldnames != HEADERS:
                raise ValueError("Fieldnames differ from GLS Standard")

            self.currency_code = "EUR"
            self.account_number = ""

            # this holds the statements to be imported into odoo
            self.bank_statement_data = []

            # this holds the statement lines
            self.transactions = []

            # this holds data which will not be imported,
            # but needed for computation
            self.meta = []

            for row in iso8859_proxy(reader):
                row = Row(row) # your boat, gently down the stream

                # make new statement when account number changes
                if all([
                    len(self.account_number) > 0,
                    row.raw["Kontonummer"] != self.account_number
                ]):
                    self._append_bank_statement()
                    return (
                        self.currency_code,
                        self.account_number,
                        self.bank_statement_data
                    )

                self.account_number = row.raw["Kontonummer"]

                self.transactions.append(row.items())
                self.transactions[-1]["name"]

                for i in account_invoice:
                    if i.reference in row.ref:
                        self.transactions[-1]["name"] = i.reference
                        break
                    if i.number in row.ref:
                        self.transactions[-1]["name"] = i.number
                        break

                    sale_order = self.env["sale.order"].search([
                        ('invoice_ids', 'in', [i.id])
                    ])
                    for i_i in sale_order:
                        if i_i.name in row.ref:
                            self.transactions[-1]["name"] = i_i.name
                            break

                meta = {}
                # set Kontostand to 0, when its empty
                try:
                    meta["Kontostand"] = monetize(row.raw["Kontostand"])
                except ValueError:
                    meta["Kontostand"] = 0.0

                self.meta.append({
                    "Kontostand": meta["Kontostand"],
                    "Betrag": row.amount
                })

            self._append_bank_statement()
            return (
                self.currency_code,
                self.account_number,
                self.bank_statement_data
            )
        except ValueError, e:
            return super(
                AccountBankStatementImport, self)._parse_file(data_file)

    def _append_bank_statement(self):
        """
        to be called after Kontostand and Betrag are in self.meta
        """
        bsd = {
            # csv is ordered top down wtf
            # get the newest date in transactions
            "date": max(map(lambda x: x["date"], self.transactions)),
            "balance_start": reduce(operator.add, (
                self.meta[-1]["Kontostand"],
                self.meta[-1]["Betrag"]
            )),
            # balance end is the last Kontostand
            "balance_end_real": self.meta[0]["Kontostand"],
            "transactions": self.transactions
        }

        abs = self.env["account.bank.statement"].search([],
            order = "date desc", limit = 1)

        if len(abs) and tools.float_compare(
            abs.mapped("balance_end_real")[0],
            bsd["balance_start"],
            precision_digits = 2
        ) != 0:
            self.notifications.append({
                "type": "warning",
                "message": _("Bank Statements are discontinous")
            })

        self.bank_statement_data.append(bsd)

        self.transactions = []
        self.meta = []

    def _create_bank_statements(self, stmts_vals):
        statement_ids, notifications = super(
            AccountBankStatementImport, self)._create_bank_statements(
                stmts_vals)

        notifications += self.notifications

        return statement_ids, notifications


class Row(object):
    def __init__(self, row):
        self._row = row

    @property
    def amount(self):
        return monetize(self._row["Betrag"])

    @property
    def date(self):
        return datetime.strptime(
            self._row["Buchungstag"], "%d.%m.%Y").strftime(
                "%Y-%m-%d")

    @property
    def ref(self):
        return " ".join((
            # VWZ1-14
            self._row["VWZ{0}".format(i + 1)] for i in range(14)
        ))

    @property
    def name(self):
        return self._row["Buchungstext"]

    @property
    def partner_name(self):
        return self._row[u"Auftraggeber/Empfänger"]

    @property
    def raw(self):
        return self._row

    def items(self):
        return {
            "amount": self.amount,
            "date": self.date,
            "ref": self.ref,
            "name": self.name,
            "partner_name": self.partner_name
        }
