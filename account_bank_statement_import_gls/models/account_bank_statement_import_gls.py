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
    for row in reader:
        ret = {iso8859_utf8(k): iso8859_utf8(v) for k, v in row.items()}
        yield ret

def monetize(s):
    return float(s.replace(".", "").replace(",", "."))

class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    @property
    def notifications(self):
        if getattr(self, "_notifications", None) is None:
            self._notifications = []
        return self._notifications

    def _parse_file(self, data_file):
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
                # make new statement when account number changes
                if all([
                    len(self.account_number) > 0,
                    row["Kontonummer"] != self.account_number
                ]):
                    self._append_bank_statement()
                    return (
                        self.currency_code,
                        self.account_number,
                        self.bank_statement_data
                    )

                self.account_number = row["Kontonummer"]

                self.transactions.append({
                    "name": " ".join((
                        row["VWZ{0}".format(i + 1)] for i in range(14)
                    )),
                    "date": datetime.strptime(
                        row["Buchungstag"], "%d.%m.%Y").strftime(
                            "%Y-%m-%d"),
                    "amount": monetize(row["Betrag"]),
                    "partner_name": row[u"Auftraggeber/Empfänger"]
                })

                self.meta.append({
                    "Kontostand": monetize(row["Kontostand"]),
                    "Betrag": monetize(row["Betrag"])
                })

            self._append_bank_statement()
            return (
                self.currency_code,
                self.account_number,
                self.bank_statement_data
            )
        except ValueError, e:
            print e
            return super(
                AccountBankStatementImport, self)._parse_file(data_file)

    def _append_bank_statement(self):
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
