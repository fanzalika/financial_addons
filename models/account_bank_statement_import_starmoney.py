# -*- coding: utf-8 -*-
import pandas as pd
from StringIO import StringIO

from openerp import models


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    @property
    def notifications(self):
        if getattr(self, "_notifications", None) is None:
            self._notifications = []
        return self._notifications

    def _parse_file(self, data_file):
        try:
            datafile = StringIO(data_file)
            dataset = pd.read_csv(
                datafile,
                encoding='utf-8-sig',
                sep=';', quotechar='"',
                names=['date', 'partner', 'description', 'amount', 'saldo'],
                skiprows=1,
                parse_dates=['date'], dayfirst=True,
                decimal=',',
            ).dropna(how='any')

            currency_codes = set(
                amount.split(' ')[-1] for amount in dataset['amount']
            )

            if len(currency_codes) > 1:
                raise ValueError()

            # float foo
            dataset['amount'] = [
                amount.replace('.', '').replace(',', '.').replace(' EUR', '')
                for amount in dataset['amount']
            ]

            dataset = dataset.convert_objects(convert_numeric=True)

            rows = dataset[::-1].iterrows()

            currency_code = 'EUR'
            account_number = None

            bank_statement_data = [{
                "date": max(dataset['date']).strftime('%Y-%m-%d'),
                "transactions": [{
                    "name": row["description"],
                    "date": row["date"].strftime('%Y-%m-%d'),
                    "amount": row["amount"],
                    # "account_number": row["account_number"],
                    "partner_name": row["partner"]
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
