# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ScenarioTest, record_only


class AzureReservationsTests(ScenarioTest):

    def _validate_reservation_order(self, reservation_order):
        self.assertIsNotNone(reservation_order)
        self.assertTrue(reservation_order['etag'])
        self.assertTrue(reservation_order['id'])
        self.assertTrue(reservation_order['name'])
        self.assertTrue(reservation_order['originalQuantity'])
        self.assertTrue(reservation_order['provisioningState'])
        self.assertTrue(reservation_order['requestDateTime'])
        self.assertTrue(reservation_order['reservations'])
        self.assertTrue(reservation_order['term'])
        self.assertTrue(reservation_order['type'])
        self.assertTrue(reservation_order['type'] == 'Microsoft.Capacity/reservationOrders')

    def _validate_reservation(self, reservation):
        self.assertIsNotNone(reservation)
        self.assertTrue(reservation['location'])
        self.assertTrue(len(reservation['location']) > 0)
        self.assertTrue(reservation['etag'])
        self.assertTrue(reservation['etag'] > 0)
        self.assertTrue(reservation['id'])
        self.assertTrue(reservation['name'])
        self.assertTrue(reservation['sku'])
        self.assertTrue(reservation['properties'])
        self.assertTrue(reservation['type'])
        self.assertTrue(reservation['type'] == 'Microsoft.Capacity/reservationOrders/reservations')

    @record_only()  # This test relies on a subscription id with the existing reservation orders
    def test_get_applied_reservation_order_ids(self):
        self.kwargs.update({
            'subscription': '00000000-0000-0000-0000-000000000000'
        })
        result = self.cmd('reservations reservation-order-id list --subscription-id {subscription}') \
            .get_output_in_json()
        for order_id in result['reservationOrderIds']['value']:
            self.assertIn('/providers/Microsoft.Capacity/reservationorders/', order_id)

    @record_only()  # This test relies on the existing reservation order
    def test_list_reservation_order(self):
        reservation_order_list = self.cmd('reservations reservation-order list').get_output_in_json()
        self.assertIsNotNone(reservation_order_list)
        for order in reservation_order_list:
            self._validate_reservation_order(order)
            self.assertIn('/providers/microsoft.capacity/reservationOrders/', order['id'])
            self.assertGreater(order['etag'], 0)
            for reservation in order['reservations']:
                self.assertTrue(reservation['id'])

    @record_only()  # This test relies on the existing reservation order
    def test_get_reservation_order(self):
        self.kwargs.update({
            'reservation_order_id': '0a47417c-cd30-4f67-add6-d631583e09f3'
        })
        command = 'reservations reservation-order show --reservation-order-id {reservation_order_id}'
        reservation_order = self.cmd(command).get_output_in_json()
        self._validate_reservation_order(reservation_order)
        self.assertIn('/providers/microsoft.capacity/reservationOrders/', reservation_order['id'])
        self.assertGreater(reservation_order['etag'], 0)

    @record_only()  # This test relies on the existing reservation order
    def test_list_reservation(self):
        self.kwargs.update({
            'reservation_order_id': '0a47417c-cd30-4f67-add6-d631583e09f3'
        })
        reservation_list = self.cmd('reservations reservation list --reservation-order-id {reservation_order_id}') \
            .get_output_in_json()
        self.assertIsNotNone(reservation_list)
        for reservation in reservation_list:
            self.assertIn(self.kwargs['reservation_order_id'], reservation['name'])
            self.assertGreater(reservation['etag'], 0)
            self.assertEqual('Microsoft.Capacity/reservationOrders/reservations', reservation['type'])

    @record_only()  # This test relies on the existing reservation order
    def test_get_reservation(self):
        self.kwargs.update({
            'reservation_order_id': '0a47417c-cd30-4f67-add6-d631583e09f3',
            'reservation_id': 'ae1fbdad-6333-4964-9f4c-83f7e2b7f44f'
        })
        reservation = self.cmd('reservations reservation show  --reservation-order-id {reservation_order_id} '
                               '--reservation-id {reservation_id}').get_output_in_json()
        self.assertIn(self.kwargs['reservation_order_id'], reservation['name'])
        self.assertGreater(reservation['etag'], 0)
        self.assertGreater(reservation['properties']['quantity'], 0)
        self.assertEqual('Microsoft.Capacity/reservationOrders/reservations', reservation['type'])

    @record_only()  # This test relies on the existing reservation order
    def test_list_reservation_history(self):
        self.kwargs.update({
            'reservation_order_id': '0a47417c-cd30-4f67-add6-d631583e09f3',
            'reservation_id': 'ae1fbdad-6333-4964-9f4c-83f7e2b7f44f'
        })
        history = self.cmd('reservations reservation list-history --reservation-order-id {reservation_order_id}'
                           ' --reservation-id {reservation_id}').get_output_in_json()
        self.assertGreater(len(history), 0)
        for entry in history:
            self.assertGreater(entry['etag'], 0)
            name_format = '{}/{}'.format(self.kwargs['reservation_order_id'], self.kwargs['reservation_id'])
            self.assertIn(name_format, entry['name'])

    @record_only()  # This test relies on a subscription with reservation permissions
    def test_get_catalog(self):
        self.kwargs.update({
            'subscription': '00000000-0000-0000-0000-000000000000',
            'type': 'VirtualMachines',
            'location': 'westus'
        })
        catalog = self.cmd(
            'reservations catalog show --subscription-id {subscription} --reserved-resource-type {type} --location {location}').get_output_in_json()
        self.assertGreater(len(catalog), 0)
        for entry in catalog:
            self.assertGreater(len(entry['terms']), 0)
            self.assertGreater(len(entry['skuProperties']), 0)
            self.assertIsNotNone(entry['resourceType'])
            self.assertIsNotNone(entry['name'])

    @record_only()  # This test relies on the existing reservation order
    def test_update_reservation(self):
        self.kwargs.update({
            'reservation_order_id': 'fe1341ea-4820-4ac9-9352-4136a6d8a252',
            'reservation_id': '8e5963e2-000b-45bd-a1b4-305c9e5f89c9',
            'scope': '/subscriptions/d3ae48e5-dbb2-4618-afd4-fb1b8559cb80',
            'instance_flexibility': 'Off'
        })

        single_reservation = self.cmd('reservations reservation update --reservation-order-id {reservation_order_id}'
                                      ' --reservation-id {reservation_id} -t Single -s {scope}'
                                      ' --instance-flexibility {instance_flexibility}').get_output_in_json()
        self.assertEqual('Single', single_reservation['properties']['appliedScopeType'])

        shared_reservation = self.cmd('reservations reservation update --reservation-order-id {reservation_order_id} '
                                      '--reservation-id {reservation_id} -t Shared'
                                      ' --instance-flexibility {instance_flexibility}').get_output_in_json()
        self.assertEqual('Shared', shared_reservation['properties']['appliedScopeType'])

    @record_only()  # This test relies on the existing reservation order
    def test_split_and_merge(self):
        self.kwargs.update({
            'reservation_order_id': '0af601f3-7868-44ee-b833-4d2e64ad3d70',
            'reservation_id': '6dee7663-3e63-4115-aa4d-41e9a57f551e',
            'quantity1': 1,
            'quantity2': 2
        })

        original_reservation = self.cmd('reservations reservation show  --reservation-order-id {reservation_order_id}'
                                        ' --reservation-id {reservation_id}').get_output_in_json()
        original_quantity = original_reservation['properties']['quantity']

        split_items = self.cmd('reservations reservation split --reservation-order-id {reservation_order_id} '
                               '--reservation-id {reservation_id} -1 {quantity1} -2 {quantity2}').get_output_in_json()
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

    @record_only()  # This test relies on a subscription with reservation permissions
    def test_calculate_reservation_order(self):
        self.kwargs.update({
            'subid': 'd3ae48e5-dbb2-4618-afd4-fb1b8559cb80',
            'sku': 'standard_b1ls',
            'location': 'westus',
            'reservedResourceType': 'VirtualMachines',
            'term': 'P1Y',
            'quantity': '2',
            'displayName': 'test',
            'appliedScopes': 'Shared',
            'instanceFlexibility': 'Off',
            'billingPlan': 'Monthly',
            'appliedScopeType': 'Shared'
        })
        response = self.cmd('reservations reservation-order calculate --sku {sku} --location {location} --reserved-resource-type {reservedResourceType}'
                            ' --billing-scope {subid} --term {term} --billing-plan {billingPlan} --display-name {displayName}'
                            ' --quantity {quantity} --applied-scope-type {appliedScopeType}').get_output_in_json()
        self.assertIsNotNone(response)
        self.assertIsNotNone(response['properties']['reservationOrderId'])
        self.assertEqual('standard_b1ls', response['properties']['skuDescription'])

    @record_only()  # This test relies on a subscription with reservation purchase permissions
    def test_purchase_reservation_order(self):
        self.kwargs.update({
            'roid': 'd4ef7ec2-941c-4da7-8ec9-2f148255a0dc',
            'subid': 'd3ae48e5-dbb2-4618-afd4-fb1b8559cb80',
            'sku': 'standard_b1ls',
            'location': 'westus',
            'reservedResourceType': 'VirtualMachines',
            'term': 'P1Y',
            'quantity': '2',
            'displayName': 'test',
            'appliedScopes': 'Shared',
            'instanceFlexibility': 'Off',
            'billingPlan': 'Monthly',
            'appliedScopeType': 'Shared'
        })
        response = self.cmd('reservations reservation-order purchase --reservation-order-id {roid} --sku {sku} --location {location} --reserved-resource-type {reservedResourceType}'
                            ' --billing-scope {subid} --term {term} --billing-plan {billingPlan} --display-name {displayName}'
                            ' --quantity {quantity} --applied-scope-type {appliedScopeType}').get_output_in_json()
        self.assertIsNotNone(response)
        self.assertGreater(response['etag'], 0)
        self.assertIsNotNone(response['term'])
        self.assertIsNotNone(response['billingPlan'])
        self.assertIsNotNone(response['displayName'])
        self.assertEqual(2, response['originalQuantity'])
