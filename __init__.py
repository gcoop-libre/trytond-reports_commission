# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import commission


def register():
    Pool.register(
        commission.CommissionReportStart,
        commission.CommissionWrapper,
        module='reports_commission', type_='model')
    Pool.register(
        commission.CommissionReport,
        module='reports_commission', type_='report')
    Pool.register(
        commission.CommissionReportWiz,
        module='reports_commission', type_='wizard')
