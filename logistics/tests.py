from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User, Shipment, ShipmentStatusLog


class LogisticsAPITests(APITestCase):
    def setUp(self):
        # Create users for testing
        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='Password123!',
            role=User.Role.ADMIN
        )
        self.driver_user = User.objects.create_user(
            username='driver_john',
            email='driver@example.com',
            password='Password123!',
            role=User.Role.DRIVER,
            phone_number='1234567890'
        )
        self.customer_user = User.objects.create_user(
            username='customer_jane',
            email='jane@example.com',
            password='Password123!',
            role=User.Role.CUSTOMER
        )
        self.other_customer = User.objects.create_user(
            username='customer_bob',
            email='bob@example.com',
            password='Password123!',
            role=User.Role.CUSTOMER
        )

    def test_user_registration(self):
        url = reverse('user-list')
        data = {
            'username': 'new_customer',
            'email': 'new@example.com',
            'password': 'StrongPassword123!',
            'role': User.Role.CUSTOMER,
            'phone_number': '5551234'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='new_customer').exists())
        self.assertNotIn('password', response.data)

    def test_jwt_authentication_and_token_refresh(self):
        # Login
        login_url = reverse('token_obtain_pair')
        login_data = {
            'username': 'customer_jane',
            'password': 'Password123!'
        }
        response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        access_token = response.data['access']
        refresh_token = response.data['refresh']

        # Refresh token
        refresh_url = reverse('token_refresh')
        refresh_response = self.client.post(refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)

        # Authenticated request to /me
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        me_url = reverse('user-me')
        me_response = self.client.get(me_url)
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data['username'], 'customer_jane')

    def test_shipment_creation_and_auto_tracking(self):
        self.client.force_authenticate(user=self.customer_user)
        url = reverse('shipment-list')
        data = {
            'delivery_address': '123 Main St, Springfield',
            'pickup_address': '456 Elm St, Shelbyville',
            'weight_kg': '15.50'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['tracking_number'].startswith('TRK-'))
        self.assertEqual(response.data['status'], Shipment.Status.PENDING)
        self.assertEqual(response.data['customer'], str(self.customer_user))

        # Verify initial status log
        shipment = Shipment.objects.get(id=response.data['id'])
        self.assertEqual(shipment.status_logs.count(), 1)
        self.assertEqual(shipment.status_logs.first().status, Shipment.Status.PENDING)

    def test_shipment_rbac_query_filtering(self):
        # Create shipment for Jane
        shipment_jane = Shipment.objects.create(
            customer=self.customer_user,
            delivery_address='Address 1',
            pickup_address='Address 2',
            driver=self.driver_user
        )
        # Create shipment for Bob
        shipment_bob = Shipment.objects.create(
            customer=self.other_customer,
            delivery_address='Address 3',
            pickup_address='Address 4'
        )

        url = reverse('shipment-list')

        # Customer Jane sees only her shipment
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], shipment_jane.id)

        # Driver John sees assigned shipment
        self.client.force_authenticate(user=self.driver_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], shipment_jane.id)

        # Admin sees all shipments
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_admin_assign_driver(self):
        shipment = Shipment.objects.create(
            customer=self.customer_user,
            delivery_address='123 Market St',
            pickup_address='Warehouse A'
        )
        url = reverse('shipment-assign-driver', kwargs={'pk': shipment.pk})

        # Admin can assign valid driver
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(url, {'driver_id': self.driver_user.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], Shipment.Status.ASSIGNED)
        self.assertEqual(response.data['driver'], str(self.driver_user))

        # Assigning a non-driver user should fail
        response = self.client.patch(url, {'driver_id': self.customer_user.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Non-admin user cannot assign driver
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.patch(url, {'driver_id': self.driver_user.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_status_by_driver_and_admin(self):
        shipment = Shipment.objects.create(
            customer=self.customer_user,
            driver=self.driver_user,
            delivery_address='123 Market St',
            pickup_address='Warehouse A',
            status=Shipment.Status.ASSIGNED
        )
        url = reverse('shipment-update-status', kwargs={'pk': shipment.pk})

        # Driver updates status to IN_TRANSIT
        self.client.force_authenticate(user=self.driver_user)
        response = self.client.patch(url, {'status': Shipment.Status.IN_TRANSIT, 'notes': 'Picked up'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], Shipment.Status.IN_TRANSIT)

        # Status log recorded
        shipment.refresh_from_db()
        self.assertEqual(shipment.status, Shipment.Status.IN_TRANSIT)
        self.assertEqual(shipment.status_logs.count(), 1)
        self.assertEqual(shipment.status_logs.first().notes, 'Picked up')

        # Invalid status rejected
        response = self.client.patch(url, {'status': 'INVALID_STATUS'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_public_tracking_endpoint(self):
        shipment = Shipment.objects.create(
            customer=self.customer_user,
            delivery_address='456 Pine St',
            pickup_address='Origin Hub'
        )
        ShipmentStatusLog.objects.create(
            shipment=shipment,
            status=Shipment.Status.PENDING,
            notes='Package received'
        )

        # Unauthenticated request to track endpoint
        self.client.logout()
        url = reverse('track-detail', kwargs={'tracking_number': shipment.tracking_number})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['tracking_number'], shipment.tracking_number)
        self.assertEqual(len(response.data['status_logs']), 1)

        # Non-existent tracking number returns 404
        bad_url = reverse('track-detail', kwargs={'tracking_number': 'TRK-DOESNOTEXIST'})
        bad_response = self.client.get(bad_url)
        self.assertEqual(bad_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_model_string_representations(self):
        self.assertEqual(str(self.admin_user), f"admin_user ({User.Role.ADMIN})")
        shipment = Shipment.objects.create(
            customer=self.customer_user,
            delivery_address='A',
            pickup_address='B',
            status=Shipment.Status.PENDING
        )
        self.assertIn(shipment.tracking_number, str(shipment))
        self.assertIn("Pending Pickup", str(shipment))

    def test_api_root_and_health_check(self):
        root_res = self.client.get(reverse('api_root'))
        self.assertEqual(root_res.status_code, status.HTTP_200_OK)
        self.assertEqual(root_res.json()['status'], 'healthy')

        health_res = self.client.get(reverse('health_check'))
        self.assertEqual(health_res.status_code, status.HTTP_200_OK)
        self.assertEqual(health_res.json()['status'], 'ok')

    def test_prevent_role_escalation_by_non_admin(self):
        # Public registration cannot create ADMIN
        reg_url = reverse('user-list')
        reg_data = {
            'username': 'attempt_admin',
            'email': 'attempt@example.com',
            'password': 'Password123!',
            'role': User.Role.ADMIN
        }
        res = self.client.post(reg_url, reg_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='attempt_admin')
        self.assertEqual(user.role, User.Role.CUSTOMER)

        # Customer cannot self-promote to ADMIN via /me
        self.client.force_authenticate(user=self.customer_user)
        me_url = reverse('user-me')
        patch_res = self.client.patch(me_url, {'role': User.Role.ADMIN}, format='json')
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.customer_user.refresh_from_db()
        self.assertEqual(self.customer_user.role, User.Role.CUSTOMER)

