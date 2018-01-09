# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, record_only


@record_only()
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
        self.kwargs.update({
            'subscription': '00000000-0000-0000-0000-000000000000'
        })
        result = self.cmd('reservations reservation-order-id list --subscription-id {subscription}') \
                     .get_output_in_json()
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
        self.kwargs.update({
            'reservation_order_id': "86d9870a-bf1e-4635-94c8-b0f08932bc3a"
        })
        command = 'reservations reservation-order show --reservation-order-id {reservation_order_id}'
        reservation_order = self.cmd(command).get_output_in_json()
        self._validate_reservation_order(reservation_order)
        self.assertIn('/providers/microsoft.capacity/reservationOrders/', reservation_order['id'])
        self.assertGreater(reservation_order['etag'], 0)
        self.assertGreater(len(reservation_order['reservationsProperty']), 0)

    def test_list_reservation(self):
        self.kwargs.update({
            'reservation_order_id': "86d9870a-bf1e-4635-94c8-b0f08932bc3a"
        })
        reservation_list = self.cmd('reservations reservation list --reservation-order-id {reservation_order_id}') \
                               .get_output_in_json()
        self.assertIsNotNone(reservation_list)
        for reservation in reservation_list:
            self.assertIn(self.kwargs['reservation_order_id'], reservation['name'])
            self.assertGreater(reservation['etag'], 0)
            self.assertEqual('Microsoft.Capacity/reservationOrders/reservations', reservation['type'])

    def test_get_reservation(self):
        self.kwargs.update({
            'reservation_order_id': "86d9870a-bf1e-4635-94c8-b0f08932bc3a",
            'reservation_id': '0532ae1c-3c80-48a9-ae18-19cc2b6f4791'
        })
        reservation = self.cmd('reservations reservation show  --reservation-order-id {reservation_order_id} '
                               '--reservation-id {reservation_id}').get_output_in_json()
        self.assertIn(self.kwargs['reservation_order_id'], reservation['name'])
        self.assertGreater(reservation['etag'], 0)
        self.assertGreater(reservation['properties']['quantity'], 0)
        self.assertEqual('Microsoft.Capacity/reservationOrders/reservations', reservation['type'])

    def test_list_reservation_history(self):
        self.kwargs.update({
            'reservation_order_id': "86d9870a-bf1e-4635-94c8-b0f08932bc3a",
            'reservation_id': '0532ae1c-3c80-48a9-ae18-19cc2b6f4791'
        })
        history = self.cmd('reservations reservation list-history --reservation-order-id {reservation_order_id}'
                           ' --reservation-id {reservation_id}').get_output_in_json()
        self.assertGreater(len(history), 0)
        for entry in history:
            self.assertGreater(entry['etag'], 0)
            name_format = '{}/{}'.format(self.kwargs['reservation_order_id'], self.kwargs['reservation_id'])
            self.assertIn(name_format, entry['name'])

    def test_get_catalog(self):
        self.kwargs.update({
            'subscription': '00000000-0000-0000-0000-000000000000'
        })
        catalog = self.cmd('az reservations catalog show --subscription-id {subscription}').get_output_in_json()
        self.assertGreater(len(catalog), 0)
        for entry in catalog:
            self.assertGreater(len(entry['terms']), 0)
            self.assertGreater(len(entry['locations']), 0)
            self.assertIsNotNone(entry['resourceType'])
            self.assertIsNotNone(entry['name'])
            self.assertIsNotNone(entry['size'])

    def test_update_reservation(self):
        self.kwargs.update({
            'reservation_order_id': "86d9870a-bf1e-4635-94c8-b0f08932bc3a",
            'reservation_id': '0532ae1c-3c80-48a9-ae18-19cc2b6f4791',
            'scope': '/subscriptions/917b6752-3ac4-4087-84d7-b587adcca91b'
        })
        shared_reservation = self.cmd('reservations reservation update --reservation-order-id {reservation_order_id} '
                                      '--reservation-id {reservation_id} -t Shared').get_output_in_json()
        self.assertEqual('Shared', shared_reservation['properties']['appliedScopeType'])

        single_reservation = self.cmd('reservations reservation update --reservation-order-id {reservation_order_id}'
                                      ' --reservation-id {reservation_id} -t Single -s {scope}').get_output_in_json()
        self.assertEqual('Single', single_reservation['properties']['appliedScopeType'])

    def test_split_and_merge(self):
        self.kwargs.update({
            'reservation_order_id': "86d9870a-bf1e-4635-94c8-b0f08932bc3a",
            'reservation_id': '1b98862a-6ae2-4c20-ade6-dd55322994b4',
            'scope': '/subscriptions/917b6752-3ac4-4087-84d7-b587adcca91b'
        })

        original_reservation = self.cmd('reservations reservation show  --reservation-order-id {reservation_order_id}'
                                        ' --reservation-id {reservation_id}').get_output_in_json()
        original_quantity = original_reservation['properties']['quantity']

        split_items = self.cmd('reservations reservation split --reservation-order-id {reservation_order_id} '
                               '--reservation-id {reservation_id} -1 2 -2 3').get_output_in_json()
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

        self.kwargs.update({
            'split_id1': split_ids[0],
            'split_id2': split_ids[1]
        })
        merge_items = self.cmd('reservations reservation merge --reservation-order-id {reservation_order_id} -1 '
                               '{split_id1} -2 {split_id2}').get_output_in_json()
        self.assertIsNotNone(merge_items)
        for item in merge_items:
            self._validate_reservation(item)
            if 'Succeeded' in item['properties']['provisioningState']:
                self.assertEqual(quantity_sum, item['properties']['quantity'])
