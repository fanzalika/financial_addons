# -*- coding: utf-8 -*-
import pandas as pd
from io import BytesIO

from openerp import models

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


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    def _parse_file(self, data_file):
        try:
            datafile = BytesIO(data_file)
            dataset = pd.read_csv(
                datafile,
                encoding='iso-8859-1',
                sep=';', quotechar='"',
                parse_dates=['Buchungstag'], dayfirst=True,
                decimal=',', thousands='.',
            ).dropna(how='all')

            currency_codes = set(dataset[u'Währung'])

            if len(currency_codes) > 1:
                raise ValueError()

            if list(dataset.keys()) != HEADERS:
                raise ValueError()

            currency_code = next(iter(currency_codes))
            account_number = None

            dataset["VWZ"] = (
                dataset[
                    ["Buchungstext"] + ["VWZ" + str(i) for i in range(1, 15)]
                ].fillna('').apply(lambda x: ' '.join(x), axis=1)
            )

            rows = dataset[::-1].iterrows()

            bank_statement_data = [{
                "date": max(dataset['Buchungstag']).strftime('%Y-%m-%d'),
                "transactions": [{
                    "name": row["VWZ"],
                    "date": row["Buchungstag"].strftime('%Y-%m-%d'),
                    "amount": row["Betrag"],
                    "partner_name": row[u"Auftraggeber/Empfänger"]
                } for _, row in rows]
            }]

            return (
                currency_code,
                account_number,
                bank_statement_data
            )
        except (ValueError, KeyError):
            return super(
                AccountBankStatementImport, self)._parse_file(data_file)
