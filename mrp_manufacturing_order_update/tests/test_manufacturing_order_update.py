# -*- coding: utf8 -*-
#
# Copyright (C) 2015 NDP Systèmes (<http://www.ndp-systemes.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from datetime import *
from openerp.tests import common
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class TestOrderUpdate(common.TransactionCase):

    def setUp(self):
        super(TestOrderUpdate, self).setUp()

        self.company = self.browse_ref('base.main_company')
        self.product_to_manufacture1 = self.browse_ref('mrp_manufacturing_order_update.product_to_manufacture1')
        self.unit = self.browse_ref('product.product_uom_unit')
        self.location1 = self.browse_ref('stock.stock_location_stock')
        self.bom1 = self.browse_ref('mrp_manufacturing_order_update.bom1')
        self.assertTrue(self.bom1.bom_line_ids)
        self.line1 = self.browse_ref('mrp_manufacturing_order_update.line1')
        self.line2 = self.browse_ref('mrp_manufacturing_order_update.line2')
        self.line3 = self.browse_ref('mrp_manufacturing_order_update.line3')
        self.line4 = self.browse_ref('mrp_manufacturing_order_update.line4')
        self.line5 = self.browse_ref('mrp_manufacturing_order_update.line5')
        self.line6 = self.browse_ref('mrp_manufacturing_order_update.line6')
        self.product1 = self.browse_ref('mrp_manufacturing_order_update.product1')
        self.product2 = self.browse_ref('mrp_manufacturing_order_update.product2')
        self.product3 = self.browse_ref('mrp_manufacturing_order_update.product3')

        self.mrp_production1 = self.env['mrp.production'].create({
            'name': 'mrp_production1',
            'product_id': self.product_to_manufacture1.id,
            'product_qty': 1,
            'product_uom': self.unit.id,
            'location_src_id': self.location1.id,
            'location_dest_id': self.location1.id,
            'date_planned': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'bom_id': self.bom1.id,
            'company_id': self.company.id,
        })
        self.mrp_production1.action_confirm()

        self.mrp_production2 = self.env['mrp.production'].create({
            'name': 'mrp_production2',
            'product_id': self.product_to_manufacture1.id,
            'product_qty': 1,
            'product_uom': self.unit.id,
            'location_src_id': self.location1.id,
            'location_dest_id': self.location1.id,
            'date_planned': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'bom_id': self.bom1.id,
            'company_id': self.company.id,
        })
        self.mrp_production2.action_confirm()

        # Let's check moves for order 1
        self.assertEqual(len(self.mrp_production1.move_lines), 6)
        self.assertEqual(len(self.mrp_production1.move_lines2), 0)
        moves_data = [[move.product_id, move.product_uom_qty, move.state] for move in self.mrp_production1.move_lines]
        self.assertIn([self.product1, 5, 'confirmed'], moves_data)
        self.assertIn([self.product2, 10, 'confirmed'], moves_data)
        self.assertIn([self.product3, 15, 'confirmed'], moves_data)
        self.assertIn([self.product1, 20, 'confirmed'], moves_data)
        self.assertIn([self.product2, 25, 'confirmed'], moves_data)
        self.assertIn([self.product3, 30, 'confirmed'], moves_data)

        # Let's check product_lines for order 1
        self.assertEqual(len(self.mrp_production1.product_lines), 6)
        lines_data = [[line.product_id, line.product_qty] for line in self.mrp_production1.product_lines]
        self.assertIn([self.product1, 5], lines_data)
        self.assertIn([self.product2, 10], lines_data)
        self.assertIn([self.product3, 15], lines_data)
        self.assertIn([self.product1, 20], lines_data)
        self.assertIn([self.product2, 25], lines_data)
        self.assertIn([self.product3, 30], lines_data)

        self.assertEqual(self.mrp_production1.state, 'confirmed')
        self.assertEqual(self.mrp_production2.state, 'confirmed')

        # Let's check moves for order 2
        self.assertEqual(len(self.mrp_production2.move_lines), 6)
        self.assertEqual(len(self.mrp_production2.move_lines2), 0)
        moves_data = [[move.product_id, move.product_uom_qty, move.state] for move in self.mrp_production2.move_lines]
        self.assertIn([self.product1, 5, 'confirmed'], moves_data)
        self.assertIn([self.product2, 10, 'confirmed'], moves_data)
        self.assertIn([self.product3, 15, 'confirmed'], moves_data)
        self.assertIn([self.product1, 20, 'confirmed'], moves_data)
        self.assertIn([self.product2, 25, 'confirmed'], moves_data)
        self.assertIn([self.product3, 30, 'confirmed'], moves_data)

        # Let's check product_lines for order 2
        self.assertEqual(len(self.mrp_production2.product_lines), 6)
        lines_data = [[line.product_id, line.product_qty] for line in self.mrp_production2.product_lines]
        self.assertIn([self.product1, 5], lines_data)
        self.assertIn([self.product2, 10], lines_data)
        self.assertIn([self.product3, 15], lines_data)
        self.assertIn([self.product1, 20], lines_data)
        self.assertIn([self.product2, 25], lines_data)
        self.assertIn([self.product3, 30], lines_data)

    def test_10_order_quantity_calculation(self):

        self.assertTrue(self.mrp_production2.product_lines)

        # definition of function test_quantities to check that move_lines is matching the needs of product_lines

        def test_quantity(product, mrp_production):
            self.assertTrue(product in [x.product_id for x in mrp_production.product_lines])
            needed_qty = sum([y.product_qty for y in mrp_production.product_lines if y.product_id == product])
            ordered_qty = sum(
                [z.product_qty for z in mrp_production.move_lines if z.product_id == product and z.state != 'cancel'])
            self.assertEqual(needed_qty, ordered_qty)

        def test_quantities(mrp_production):
            list_products_needed = []
            for item in mrp_production.product_lines:
                if item.product_id not in list_products_needed:
                    list_products_needed += [item.product_id]
            for product in list_products_needed:
                test_quantity(product, mrp_production)
            for item in mrp_production.move_lines:
                self.assertIn(item.product_id, list_products_needed)

        # test of function button_update

        def test_update(list_qty_to_change, list_line_to_delete, list_line_to_add):
            for item in list_qty_to_change:
                item[0].product_qty = item[1]
            for item in list_line_to_delete:
                item.unlink()
            for dict in list_line_to_add:
                dict['product_uom'] = self.unit.id
                dict['bom_id'] = self.bom1.id
                self.env['mrp.bom.line'].create(dict)
            self.mrp_production1.button_update()
            test_quantities(self.mrp_production1)

        test_update([[self.line1, 10]], [], [])  # increase one quantity
        test_update([[self.line1, 15], [self.line2, 15], [self.line4, 25], [self.line5, 30]], [], [])
                    # increase two different quantities for two different product
        test_update([[self.line2, 5]], [], [])  # decrease one quantity with one move to cancel
        test_update([[self.line3, 1], [self.line6, 5]], [], [])  # decrease two quantities with two moves to cancel
        test_update([[self.line1, 5], [self.line2, 10], [self.line4, 20], [self.line5, 25]], [], [])
                    # decrease two different quantities for two different product, one move for each to delete
        test_update([[self.line1, 1], [self.line2, 1], [self.line4, 1], [self.line5, 1]], [], [])
                    # decrease two different quantities for two different product, two moves for each to delete
        test_update([[self.line1, 5], [self.line2, 10], [self.line4, 20], [self.line5, 25]], [], [])
                    # back to first quantities
        test_update([[self.line1, 10], [self.line2, 9], [self.line4, 25], [self.line5, 24]], [], [])
                    # for each product 1&2, one quantity decreases, the other one increases,
                    # new need superior to first need
        test_update([[self.line1, 11], [self.line2, 1], [self.line4, 1], [self.line5, 25]], [], [])
                    # for each product 1&2, one quantity decreases, the other one increases,
                    # new need inferior to first need, several moves to delete for each
        test_update([], [self.line1], [])  # deletion of one line
        test_update([], [self.line2, self.line3], [])  # deletion of two lines
        new_line0 = {'product_id': self.product1.id, 'product_qty': 5}
        test_update([], [], [new_line0])  # creation of one line
        new_line1 = {'product_id': self.product2.id, 'product_qty': 10}
        new_line2 = {'product_id': self.product3.id, 'product_qty': 15}
        test_update([], [], [new_line1, new_line2])  # creation of two lines
        test_update([[self.line4, 100], [self.line6, 1]], [self.line5], [new_line1, new_line2])
                    # everything together : one quantity increase, another decrease, a line is
                    # deleted and two others created

        # testing modifications of field product_lines (function write from model mrp.production)
        # afterwards, function used tu update moves is the same as before: useless to test it again

        for item in self.mrp_production2.product_lines:
            if item.product_qty == 5:
                l1 = item.id
            if item.product_qty == 10:
                l2 = item.id
            if item.product_qty == 15:
                l3 = item.id
            if item.product_qty == 20:
                l4 = item.id
            if item.product_qty == 25:
                l5 = item.id
            if item.product_qty == 30:
                l6 = item.id
        self.assertTrue(l1)
        self.assertTrue(l2)
        self.assertTrue(l3)
        self.assertTrue(l4)
        self.assertTrue(l5)
        self.assertTrue(l6)

        # changing a line quantity
        vals = {'product_lines': [[1, l1, {'product_qty': 10}], [4, l2, False], [4, l3, False], [4, l4, False],
                                  [4, l5, False], [4, l6, False]]}
        self.mrp_production2.write(vals)
        test_quantities(self.mrp_production2)

        # deleting a line :
        vals = {'product_lines': [[4, l1, False], [4, l2, False], [4, l3, False], [4, l4, False], [4, l5, False],
                                  [2, l6, False]]}
        self.mrp_production2.write(vals)
        test_quantities(self.mrp_production2)

        # adding a line
        vals = {'product_lines': [[4, l1, False], [4, l2, False], [4, l3, False], [4, l4, False], [4, l5, False],
                                  [0, False, {'product_uos_qty': 0,
                                              'name': 'a',
                                              'product_uom': 1,
                                              'product_qty': 10,
                                              'product_uos': False,
                                              'product_id': self.product2.id}]]}
        self.mrp_production2.write(vals)
        test_quantities(self.mrp_production2)

    def test_20_increase_order_qty(self):

        # Let's increase order quantity
        wizard = self.env['change.production.qty'].with_context(active_id=self.mrp_production1.id,
                                                                active_ids=[self.mrp_production1.id]).create({})
        self.assertEqual(wizard.product_qty, 1)
        wizard.product_qty = 2
        wizard.change_prod_qty()

        self.assertEqual(self.mrp_production1.product_qty, 2)

        # Let's check production moves
        self.assertEqual(len(self.mrp_production1.move_created_ids), 1)
        self.assertEqual(self.mrp_production1.move_created_ids.product_uom_qty, 2)

        # Let's check product_lines
        self.assertEqual(sum([line.product_qty for
                              line in self.mrp_production1.product_lines if line.product_id == self.product1]), 50)
        self.assertEqual(sum([line.product_qty for
                              line in self.mrp_production1.product_lines if line.product_id == self.product2]), 70)
        self.assertEqual(sum([line.product_qty for
                              line in self.mrp_production1.product_lines if line.product_id == self.product3]), 90)

        # Let's check raw material moves
        self.assertFalse(self.mrp_production1.move_lines2)
        self.assertEqual(len(self.mrp_production1.move_lines), 9)
        moves_data = [[move.product_id, move.product_uom_qty, move.state] for move in self.mrp_production1.move_lines]
        self.assertIn([self.product1, 5, 'confirmed'], moves_data)
        self.assertIn([self.product2, 10, 'confirmed'], moves_data)
        self.assertIn([self.product3, 15, 'confirmed'], moves_data)
        self.assertIn([self.product1, 20, 'confirmed'], moves_data)
        self.assertIn([self.product2, 25, 'confirmed'], moves_data)
        self.assertIn([self.product3, 30, 'confirmed'], moves_data)
        self.assertIn([self.product1, 25, 'confirmed'], moves_data)
        self.assertIn([self.product2, 35, 'confirmed'], moves_data)
        self.assertIn([self.product3, 45, 'confirmed'], moves_data)

    def test_30_decrease_order_qty(self):

        # Let's decrease order quantity
        wizard = self.env['change.production.qty'].with_context(active_id=self.mrp_production1.id,
                                                                active_ids=[self.mrp_production1.id]).create({})
        self.assertEqual(wizard.product_qty, 1)
        wizard.product_qty = 0.5
        wizard.change_prod_qty()

        self.assertEqual(self.mrp_production1.product_qty, 0.5)

        # Let's check production moves
        self.assertEqual(len(self.mrp_production1.move_created_ids), 1)
        self.assertEqual(self.mrp_production1.move_created_ids.product_uom_qty, 0.5)

        # Let's check product_lines
        self.assertEqual(sum([line.product_qty for
                              line in self.mrp_production1.product_lines if line.product_id == self.product1]), 12.5)
        self.assertEqual(sum([line.product_qty for
                              line in self.mrp_production1.product_lines if line.product_id == self.product2]), 17.5)
        self.assertEqual(sum([line.product_qty for
                              line in self.mrp_production1.product_lines if line.product_id == self.product3]), 22.5)

        # Let's check raw material moves
        self.assertEqual(len(self.mrp_production1.move_lines2), 3)
        self.assertEqual(len(self.mrp_production1.move_lines), 6)
        moves_data1 = [[move.product_id, move.product_uom_qty, move.state] for move in self.mrp_production1.move_lines]
        self.assertIn([self.product1, 5, 'confirmed'], moves_data1)
        self.assertIn([self.product2, 10, 'confirmed'], moves_data1)
        self.assertIn([self.product3, 15, 'confirmed'], moves_data1)
        self.assertIn([self.product1, 7.5, 'confirmed'], moves_data1)
        self.assertIn([self.product2, 7.5, 'confirmed'], moves_data1)
        self.assertIn([self.product3, 7.5, 'confirmed'], moves_data1)
        moves_data2 = [[move.product_id, move.product_uom_qty, move.state] for move in self.mrp_production1.move_lines2]
        self.assertIn([self.product1, 20, 'cancel'], moves_data2)
        self.assertIn([self.product2, 25, 'cancel'], moves_data2)
        self.assertIn([self.product3, 30, 'cancel'], moves_data2)
