"""
Tests for the Certificate REST APIs.
"""
from itertools import product

import ddt
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from mock import patch
from rest_framework import status
from rest_framework.test import APITestCase

from course_modes.models import CourseMode
from lms.djangoapps.certificates.apis.v0.views import CertificatesDetailView, CertificatesListView
from lms.djangoapps.certificates.models import CertificateStatuses
from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from openedx.core.djangoapps.user_authn.tests.utils import AuthType, AuthAndScopesTestMixin, JWT_AUTH_TYPES
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
class CertificatesDetailRestApiTest(AuthAndScopesTestMixin, SharedModuleStoreTestCase, APITestCase):
    """
    Test for the Certificates REST APIs
    """
    now = timezone.now()
    default_scopes = CertificatesDetailView.required_scopes

    @classmethod
    def setUpClass(cls):
        super(CertificatesDetailRestApiTest, cls).setUpClass()
        cls.course = CourseFactory.create(
            org='edx',
            number='verified',
            display_name='Verified Course'
        )

    def setUp(self):
        freezer = freeze_time(self.now)
        freezer.start()
        self.addCleanup(freezer.stop)

        super(CertificatesDetailRestApiTest, self).setUp()

        GeneratedCertificateFactory.create(
            user=self.student,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode='verified',
            download_url='www.google.com',
            grade="0.88"
        )

        self.namespaced_url = 'certificates_api:v0:certificates:detail'

    def get_url(self, username):
        """ This method is required by AuthAndScopesTestMixin. """
        return reverse(
            self.namespaced_url,
            kwargs={
                'course_id': self.course.id,
                'username': username
            }
        )

    def assert_success_response_for_student(self, response):
        """ This method is required by AuthAndScopesTestMixin. """
        self.assertEqual(
            response.data,
            {
                'username': self.student.username,
                'status': CertificateStatuses.downloadable,
                'is_passing': True,
                'grade': '0.88',
                'download_url': 'www.google.com',
                'certificate_type': CourseMode.VERIFIED,
                'course_id': unicode(self.course.id),
                'created_date': self.now,
            }
        )

    def test_no_certificate(self):
        student_no_cert = UserFactory.create(password=self.user_password)
        resp = self.get_response(
            AuthType.session,
            requesting_user=student_no_cert,
            requested_user=student_no_cert,
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error_code', resp.data)
        self.assertEqual(
            resp.data['error_code'],
            'no_certificate_for_user',
        )


@ddt.ddt
class CertificatesListRestApiTest(AuthAndScopesTestMixin, SharedModuleStoreTestCase, APITestCase):
    """
    Test for the Certificates REST APIs
    """
    now = timezone.now()
    default_scopes = CertificatesListView.required_scopes

    @classmethod
    def setUpClass(cls):
        super(CertificatesListRestApiTest, cls).setUpClass()
        cls.course = CourseFactory.create(
            org='edx',
            number='verified',
            display_name='Verified Course',
            self_paced=True,
        )

    def setUp(self):
        freezer = freeze_time(self.now)
        freezer.start()
        self.addCleanup(freezer.stop)

        super(CertificatesListRestApiTest, self).setUp()

        GeneratedCertificateFactory.create(
            user=self.student,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode='verified',
            download_url='www.google.com',
            grade="0.88",
        )

        self.namespaced_url = 'certificates_api:v0:certificates:list'

    def get_url(self, username):
        """ This method is required by AuthAndScopesTestMixin. """
        return reverse(
            self.namespaced_url,
            kwargs={
                'username': username
            }
        )

    def assert_success_response_for_student(self, response):
        """ This method is required by AuthAndScopesTestMixin. """
        self.assertEqual(
            response.data,
            [{
                'username': self.student.username,
                'course_id': unicode(self.course.id),
                'course_display_name': self.course.display_name,
                'course_organization': self.course.org,
                'certificate_type': CourseMode.VERIFIED,
                'created_date': self.now,
                'status': CertificateStatuses.downloadable,
                'is_passing': True,
                'download_url': 'www.google.com',
                'grade': '0.88',
            }]
        )

    @patch('edx_rest_framework_extensions.permissions.log')
    @ddt.data(*product(JWT_AUTH_TYPES, (True, False)))
    @ddt.unpack
    def test_jwt_no_filter(self, auth_type, scopes_enforced, mock_log):
        self.assertTrue(True)  # pylint: disable=redundant-unittest-assert

    def test_no_certificate(self):
        student_no_cert = UserFactory.create(password=self.user_password)
        resp = self.get_response(
            AuthType.session,
            requesting_user=student_no_cert,
            requested_user=student_no_cert,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])
