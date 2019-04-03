# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import doctest
import unittest
from decimal import Decimal

import trytond.tests.test_tryton
from trytond.exceptions import UserError
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.transaction import Transaction

from trytond.modules.company.tests import create_company, set_company


class TestCase(ModuleTestCase):
    'Test module'
    module = 'stock_location_group'

    @with_transaction()
    def test_location_access(self):
        'Test location access'
        pool = Pool()
        User = pool.get('res.user')
        Group = pool.get('res.group')
        Location = pool.get('ir.model.access')
        Template = pool.get('product.template')
        Product = pool.get('product.product')
        Uom = pool.get('product.uom')
        Location = pool.get('stock.location')
        Move = pool.get('stock.move')

        # Create Company
        company = create_company()
        with set_company(company):
            kg, = Uom.search([('name', '=', 'Kilogram')])
            template, = Template.create([{
                        'name': 'Test location access',
                        'type': 'goods',
                        'list_price': Decimal(1),
                        'cost_price_method': 'fixed',
                        'default_uom': kg.id,
                        }])
            product, = Product.create([{
                        'template': template.id,
                        'cost_price': Decimal(0),
                        }])
            supplier, = Location.search([('code', '=', 'SUP')])
            storage, = Location.search([('code', '=', 'STO')])
            customer, = Location.search([('code', '=', 'CUS')])

            group, = Group.create([{'name': 'Restricted locations'}])

            def do_move(from_location, to_location):
                move, = Move.create([{
                            'product': product.id,
                            'uom': kg.id,
                            'quantity': 1.0,
                            'from_location': from_location.id,
                            'to_location': to_location.id,
                            'unit_price': Decimal('1'),
                            }])
                Move.do([move])

            # No problem with no restriction
            do_move(supplier, storage)

            # Restricted location
            Location.write([supplier], {'outputs_group': group.id})

            # Unable to do output move
            access_error = ('You do not have permissions to move products '
                'from location "%(location)s".')
            with self.assertRaises(UserError) as cm:
                do_move(supplier, storage)
            self.assertEqual(cm.exception.message,
                access_error % {'location': supplier.rec_name})

            # No problem doing input move
            do_move(storage, supplier)
            do_move(storage, customer)

            # Restricted input location
            Location.write([customer], {'inputs_group': group.id})
            with self.assertRaises(UserError) as cm:
                do_move(storage, customer)
            self.assertEqual(cm.exception.message,
                access_error % {'location': customer.rec_name})

            # No problem if user belongs to restricted group
            User.write([User(Transaction().user)], {
                    'groups': [('add', [group.id])],
                    })
            do_move(supplier, storage)
            do_move(storage, customer)


def suite():
    suite = trytond.tests.test_tryton.suite()
    from trytond.modules.company.tests import test_company
    for test in test_company.suite():
        if test not in suite and not isinstance(test, doctest.DocTestCase):
            suite.addTest(test)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCase))
    return suite
