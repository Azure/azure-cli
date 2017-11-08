# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest


class AzureReservationsTests(ScenarioTest):

    def _validate_reservation_order(self, reservation_order):
        self.assertIsNotNone(reservation_order)
        self.assertTrue(reservation_order['etag'])
        self.assertTrue(reservation_order['id'])
        self.assertTrue(reservation_order['name'])
        self.assertTrue(reservation_order['reservationsProperty'])
        self.assertTrue(reservation_order['displayName'])

    def _validate_reservation(self, reservation):
        self.assertIsNotNone(reservation)
        self.assertTrue(reservation['id'])
        self.assertTrue(reservation['name'])
        self.assertTrue(reservation['kind'])
        self.assertTrue(reservation['sku'])
        self.assertTrue(reservation['properties'])
        self.assertTrue(reservation['type'])

    def test_get_applied_reservation_order_ids(self):
        result = self.cmd('az reservations reservation-order-id list --subscription-id 00000000-0000-0000-0000-000000000000').get_output_in_json()
        for order_id in result['reservationOrderIds']['value']:
            self.assertIn('/providers/Microsoft.Capacity/reservationorders/', order_id)

    def test_list_reservation_order(self):
        reservation_order_list = self.cmd('reservations reservation-order list').get_output_in_json()
        self.assertIsNotNone(reservation_order_list)
        for order in reservation_order_list:
            self._validate_reservation_order(order)
            self.assertIn('/providers/microsoft.capacity/reservationOrders/', order['id'])
            self.assertGreater(order['etag'], 0)
            self.assertGreater(len(order['reservationsProperty']), 0)

    def test_get_reservation_order(self):
        reservation_order_id = "86d9870a-bf1e-4635-94c8-b0f08932bc3a"
        command = 'reservations reservation-order show --reservation-order-id {}'.format(reservation_order_id)
        reservation_order = self.cmd(command).get_output_in_json()
        self._validate_reservation_order(reservation_order)
        self.assertIn('/providers/microsoft.capacity/reservationOrders/', reservation_order['id'])
        self.assertGreater(reservation_order['etag'], 0)
        self.assertGreater(len(reservation_order['reservationsProperty']), 0)

    def test_list_reservation(self):
        reservation_order_id = "86d9870a-bf1e-4635-94c8-b0f08932bc3a"
        reservation_list = self.cmd('reservations reservation list --reservation-order-id {}'.format(reservation_order_id)).get_output_in_json()
        self.assertIsNotNone(reservation_list)
        for reservation in reservation_list:
            self.assertIn(reservation_order_id, reservation['name'])
            self.assertGreater(reservation['etag'], 0)
            self.assertEqual('Microsoft.Capacity/reservationOrders/reservations', reservation['type'])

    def test_get_reservation(self):
        reservation_order_id = "86d9870a-bf1e-4635-94c8-b0f08932bc3a"
        reservation_id = "0532ae1c-3c80-48a9-ae18-19cc2b6f4791"
        get_command = 'reservations reservation show  --reservation-order-id {} --reservation-id {}'.format(reservation_order_id, reservation_id)
        reservation = self.cmd(get_command).get_output_in_json()
        self.assertIn(reservation_order_id, reservation['name'])
        self.assertGreater(reservation['etag'], 0)
        self.assertGreater(reservation['properties']['quantity'], 0)
        self.assertEqual('Microsoft.Capacity/reservationOrders/reservations', reservation['type'])

    def test_list_reservation_history(self):
        reservation_order_id = "86d9870a-bf1e-4635-94c8-b0f08932bc3a"
        reservation_id = "0532ae1c-3c80-48a9-ae18-19cc2b6f4791"
        command = 'reservations reservation list-history --reservation-order-id {} --reservation-id {}'.format(reservation_order_id, reservation_id)
        history = self.cmd(command).get_output_in_json()
        self.assertGreater(len(history), 0)
        for entry in history:
            self.assertGreater(entry['etag'], 0)
            name_format = '{}/{}'.format(reservation_order_id, reservation_id)
            self.assertIn(name_format, entry['name'])

    def test_get_catalog(self):
        catalog = self.cmd('az reservations catalog show --subscription-id 00000000-0000-0000-0000-000000000000').get_output_in_json()
        self.assertGreater(len(catalog), 0)
        for entry in catalog:
            self.assertGreater(len(entry['terms']), 0)
            self.assertGreater(len(entry['locations']), 0)
            self.assertIsNotNone(entry['resourceType'])
            self.assertIsNotNone(entry['name'])
            self.assertIsNotNone(entry['size'])

    def test_update_reservation(self):
        reservation_order_id = "86d9870a-bf1e-4635-94c8-b0f08932bc3a"
        reservation_id = "0532ae1c-3c80-48a9-ae18-19cc2b6f4791"

        update_shared = 'reservations reservation update --reservation-order-id {} --reservation-id {} -t Shared'.format(reservation_order_id, reservation_id)
        shared_reservation = self.cmd(update_shared).get_output_in_json()
        self.assertEqual('Shared', shared_reservation['properties']['appliedScopeType'])

        scope = '/subscriptions/917b6752-3ac4-4087-84d7-b587adcca91b'
        update_single = 'reservations reservation update --reservation-order-id {} --reservation-id {} -t Single -s {}'.format(reservation_order_id, reservation_id, scope)
        single_reservation = self.cmd(update_single).get_output_in_json()
        self.assertEqual('Single', single_reservation['properties']['appliedScopeType'])

    def test_split_and_merge(self):
        reservation_order_id = '86d9870a-bf1e-4635-94c8-b0f08932bc3a'
        reservation_id = '1b98862a-6ae2-4c20-ade6-dd55322994b4'
        get_command = 'reservations reservation show  --reservation-order-id {} --reservation-id {}'.format(reservation_order_id, reservation_id)
        original_reservation = self.cmd(get_command).get_output_in_json()
        original_quantity = original_reservation['properties']['quantity']

        split_command = 'reservations reservation split --reservation-order-id {} --reservation-id {} -1 2 -2 3'.format(reservation_order_id, reservation_id)
        split_items = self.cmd(split_command).get_output_in_json()
        self.assertIsNotNone(split_items)

        quantity_sum = 0
        split_ids = []
        for item in split_items:
            self._validate_reservation(item)
            if 'Succeeded' in item['properties']['provisioningState']:
                item_id = item['name'].split('/')[1]
                split_ids.append(item_id)
                quantity_sum += item['properties']['quantity']
        self.assertEqual(original_quantity, quantity_sum)
        self.assertEqual(2, len(split_ids))

        merge_command = 'reservations reservation merge --reservation-order-id {} -1 {} -2 {}'.format(reservation_order_id, split_ids[0], split_ids[1])
        merge_items = self.cmd(merge_command).get_output_in_json()
        self.assertIsNotNone(merge_items)
        for item in merge_items:
            self._validate_reservation(item)
            if 'Succeeded' in item['properties']['provisioningState']:
                self.assertEqual(quantity_sum, item['properties']['quantity'])
