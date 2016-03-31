# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import doctest
import unittest
from decimal import Decimal

import trytond.tests.test_tryton
from trytond.exceptions import UserError
from trytond.tests.test_tryton import (test_view, test_depends, POOL, DB_NAME,
    USER, CONTEXT)
from trytond.transaction import Transaction


class TestCase(unittest.TestCase):
    'Test module'

    def setUp(self):
        trytond.tests.test_tryton.install_module(
            'stock_location_outputs_group')
        self.user = POOL.get('res.user')
        self.group = POOL.get('res.group')
        self.location = POOL.get('ir.model.access')
        self.template = POOL.get('product.template')
        self.product = POOL.get('product.product')
        self.category = POOL.get('product.category')
        self.uom = POOL.get('product.uom')
        self.location = POOL.get('stock.location')
        self.move = POOL.get('stock.move')
        self.company = POOL.get('company.company')

    def test0005views(self):
        'Test views'
        test_view('stock_location_outputs_group')

    def test0006depends(self):
        'Test depends'
        test_depends()

    def test_location_access(self):
        'Test location access'
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            category, = self.category.create([{
                        'name': 'Test location access',
                        }])
            kg, = self.uom.search([('name', '=', 'Kilogram')])
            template, = self.template.create([{
                        'name': 'Test location access',
                        'type': 'goods',
                        'list_price': Decimal(1),
                        'cost_price': Decimal(0),
                        'category': category.id,
                        'cost_price_method': 'fixed',
                        'default_uom': kg.id,
                        }])
            product, = self.product.create([{
                        'template': template.id,
                        }])
            supplier, = self.location.search([('code', '=', 'SUP')])
            storage, = self.location.search([('code', '=', 'STO')])
            company, = self.company.search([
                    ('rec_name', '=', 'Dunder Mifflin'),
                    ])
            currency = company.currency
            self.user.write([self.user(USER)], {
                'main_company': company.id,
                'company': company.id,
                })
            group, = self.group.create([{'name': 'Restricted locations'}])

            def do_move(from_location, to_location):
                move, = self.move.create([{
                            'product': product.id,
                            'uom': kg.id,
                            'quantity': 1.0,
                            'from_location': from_location.id,
                            'to_location': to_location.id,
                            'company': company.id,
                            'unit_price': Decimal('1'),
                            'currency': currency.id,
                            }])
                self.move.do([move])

            # No problem with no restriction
            do_move(supplier, storage)

            # Restricted location
            self.location.write([supplier], {'outputs_group': group.id})

            # Unable to do output move
            access_error = ('You do not have permisons to move products '
                'from location "%s".')
            with self.assertRaises(UserError) as cm:
                do_move(supplier, storage)
            self.assertEqual(cm.exception.message,
                access_error % supplier.rec_name)

            # No problem doing input move
            do_move(storage, supplier)

            # No problem if user belongs to restricted group
            self.user.write([self.user(USER)], {
                    'groups': [('add', [group.id])],
                    })
            do_move(supplier, storage)


def suite():
    suite = trytond.tests.test_tryton.suite()
    from trytond.modules.company.tests import test_company
    for test in test_company.suite():
        if test not in suite and not isinstance(test, doctest.DocTestCase):
            suite.addTest(test)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCase))
    return suite
