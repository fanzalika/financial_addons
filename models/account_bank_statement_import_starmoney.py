# -*- coding: utf-8 -*-

from openerp import api, fields, models, _, tools

import tablib
import maya
import collections
import codecs
import hashlib

HEADERS = [
    "Nummer", "Buchungsdatum", "Valutadatum", "Waehrung", "Betrag",
    "Empfaengername", "Bankleitzahl", "Kontonummer", "Referenz",
    "Textschluessel", "Kategorie", "Kommentar", "Verwendungszweck_1",
    "Verwendungszweck_2", "Verwendungszweck_3", "Verwendungszweck_4",
    "Verwendungszweck_5", "Verwendungszweck_6", "Verwendungszweck_7",
    "Verwendungszweck_8", "Verwendungszweck_9", "Verwendungszweck_10",
    "Verwendungszweck_11", "Verwendungszweck_12", "Verwendungszweck_13",
    "Verwendungszweck_14"
]

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
        try:
            imported = tablib.Dataset().load(
                data_file.decode("iso-8859-1").encode("utf8"),
                format="csv", delimiter=";")
            if imported.headers != HEADERS:
                pass

            headers = {k: i for i, k in enumerate(imported.headers)}
            def k(key, row):
                return row[headers[key]]

            imported.append_col(
                lambda x: maya.parse(k("Buchungsdatum", x)), header="date")
            imported.append_col(
                lambda x: monetize(k("Betrag", x)), header="amount")
            imported.append_col(
                lambda x: ' '.join(
                    k("Verwendungszweck_{}".format(_), x) for _ in range(1, 14)),
                header="note"
            )

            headers.update({k: i for i, k in enumerate(imported.headers)})

            currency_codes = set(imported["Waehrung"])
            if len(currency_codes) != 1:
                raise ValueError()

            currency_code = currency_codes.pop()
            account_number = None

            bank_statement_data = [{
                "date": max(imported["date"]).iso8601()[:10],
                "transactions": [{
                    "name": k("note", row),
                    "date": k("date", row).iso8601()[:10],
                    "amount": k("amount", row),
                    "account_number": k("Kontonummer", row),
                    "partner_name": k("Empfaengername", row)
                } for row in reversed(imported)]
            }]

            return (
                currency_code,
                account_number,
                bank_statement_data
            )
        except ValueError:
            return super(
                AccountBankStatementImport, self)._parse_file(data_file)
