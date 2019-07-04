# The COPYRIGHT file at the top level of this repository contains the
# full copyright notices and license terms.
from decimal import Decimal
from trytond.pool import Pool
from trytond.model import fields, ModelView
from trytond.wizard import Wizard, StateView, Button, StateReport
from trytond.report import Report
from trytond.modules.product import price_digits

import logging
logger = logging.getLogger(__name__)

__all__ = ['CommissionReport', 'CommissionReportWiz',
    'CommissionReportStart', 'CommissionWrapper']


class CommissionWrapper(ModelView):
    'Commission Wrapper'
    __name__ = 'reports.commission.wrapper'

    agent = fields.Many2One('commission.agent', 'Agent')
    commissions_to_pay = fields.One2Many('commission', None, 'Commissions a pagar')
    commissions_paid = fields.One2Many('commission', None, 'Commissions pagadas')
    total_amount_to_pay = fields.Numeric('Amount to pay', digits=price_digits)
    total_amount_paid = fields.Numeric('Amount paid', digits=price_digits)


class CommissionReport(Report):
    'Commission Report'
    __name__ = 'reports.commission'

    @classmethod
    def get_commissions_to_pay(cls, clause):
        pool = Pool()
        Commission = pool.get('commission')
        clause.append(('invoice_line', '=', None))
        commissions = Commission.search(clause)
        clause.pop()
        clause.append(('invoice_line.invoice.state',
                'not in', ['paid', 'cancel']))
        commissions2 = Commission.search(clause)
        return commissions + commissions2

    @classmethod
    def get_commissions_paid(cls, clause):
        pool = Pool()
        Commission = pool.get('commission')
        clause.append(('invoice_line.invoice.state', '=', 'paid'))
        return Commission.search(clause)

    @classmethod
    def get_context(cls, records, data):
        pool = Pool()
        Agent = pool.get('commission.agent')
        _ZERO = Decimal('0')
        domain = []
        if 'agents' in data:
            domain.append(('id', 'in', data['agents']))
        agents = Agent.search(domain, order=[('party.name', 'ASC')])

        records = []
        for agent in agents:
            cwrapper = CommissionWrapper()
            cwrapper.total_amount_to_pay = _ZERO
            cwrapper.total_amount_paid = _ZERO
            cwrapper.agent = agent
            clause = [
                ('date', '>=', data['from_date']),
                ('date', '<=', data['to_date']),
                ('agent', '=', agent),
                ]

            commissions = cls.get_commissions_to_pay(clause)
            cwrapper.commissions_to_pay = [c.id for c in commissions]
            for commission in commissions:
                cwrapper.total_amount_to_pay += commission.amount

            commissions = cls.get_commissions_paid(clause)
            cwrapper.commissions_paid = [c.id for c in commissions]
            for commission in commissions:
                cwrapper.total_amount_paid += commission.amount

            records.append(cwrapper)

        report_context = super(CommissionReport, cls).get_context(
            records, data)
        return report_context


class CommissionReportStart(ModelView):
    'CommissionReportStart'
    __name__ = 'reports.commission.start'

    from_date = fields.Date('From Date', required=True)
    to_date = fields.Date('To Date', required=True)
    agents = fields.Many2Many('commission.agent', None, None, 'Agents')

    @staticmethod
    def default_from_date():
        Date = Pool().get('ir.date')
        return Date.today()

    @staticmethod
    def default_to_date():
        Date = Pool().get('ir.date')
        return Date.today()


class CommissionReportWiz(Wizard):
    'CommissionsReportWiz'
    __name__ = 'reports.commission'
    start = StateView('reports.commission.start',
        'reports_commission.commission_report_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Print', 'print_', 'tryton-print', True),
            ])
    print_ = StateReport('reports.commission')

    def do_print_(self, action):
        data = {
            'from_date': self.start.from_date,
            'to_date': self.start.to_date,
            }
        if self.start.agents:
            data.update({
            'agents': [p.id for p in self.start.agents],
            })
        return action, data
