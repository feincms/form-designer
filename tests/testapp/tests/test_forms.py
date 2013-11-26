from django.core import mail
from django.test import TestCase

from feincms.module.page.models import Page

from form_designer.models import Form, FormSubmission


class FormsTest(TestCase):
    def test_forms(self):
        form = Form.objects.create(
            title='Test contact form',
            config_json=(
                u'{"email": {"email": "info@example.com"}, "save_fs": {}}'),
        )
        form.fields.create(
            ordering=0,
            title='Subject',
            name='subject',
            type='text',
        )
        form.fields.create(
            ordering=1,
            title='Email',
            name='email',
            type='email',
        )
        form.fields.create(
            ordering=2,
            title='Body',
            name='body',
            type='longtext',
        )
        form.fields.create(
            ordering=3,
            title='Please call me',
            name='please-call-me',
            type='checkbox',
            is_required=False,
        )

        form_class = form.form()
        form_instance = form_class()

        self.assertListEqual(
            [field.name for field in form_instance],
            ['subject', 'email', 'body', 'please-call-me'])

        page = Page.objects.create(override_url='/', title='')
        page.formcontent_set.create(
            region='main',
            ordering=0,
            form=form,
            success_message='Thanks, we will get back to you',
        )

        response = self.client.get('/')

        self.assertContains(
            response,
            'method="post"',
            1,
        )
        self.assertContains(
            response,
            'action="#form{}"'.format(form.id),
            1,
        )
        self.assertContains(
            response,
            '<input',
            6,  # csrf, subject, email, checkbox, _formcontent, submit
        )
        self.assertContains(
            response,
            '<textarea',
            1,
        )

        response = self.client.post('/')

        self.assertContains(
            response,
            'This field is required',
            3,
        )

        # Not this form
        response = self.client.post('/', {
            '_formcontent': -1,
        })

        self.assertNotContains(
            response,
            'This field is required',
        )

        response = self.client.post('/', {
            '_formcontent'.format(form.id): form.id,
            'fc{}-subject'.format(form.id): 'Test',
            'fc{}-email'.format(form.id): 'invalid',
            'fc{}-body'.format(form.id): 'Hello World',
        })

        self.assertNotContains(
            response,
            'This field is required',
        )

        self.assertContains(
            response,
            'Enter a valid email address',
            1,
        )

        response = self.client.post('/', {
            '_formcontent'.format(form.id): form.id,
            'fc{}-subject'.format(form.id): 'Test',
            'fc{}-email'.format(form.id): 'valid@example.com',
            'fc{}-body'.format(form.id): 'Hello World',
        })

        self.assertContains(
            response,
            'Thanks, we will get back to you',
            1,
        )

        self.assertNotContains(
            response,
            '<form',
        )

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]

        self.assertListEqual(
            message.to,
            ['info@example.com'],
        )
        self.assertEqual(
            message.from_email,
            'no-reply@example.com',
        )
        self.assertEqual(
            message.subject,
            'Test contact form',
        )
        self.assertIn('Subject: Test\n', message.body)
        self.assertIn('Email: valid@example.com\n', message.body)
        self.assertIn('Body: Hello World\n', message.body)
        self.assertIn('Please call me: False\n', message.body)

        # Exactly one submission
        submission = FormSubmission.objects.get()

        self.assertEqual(
            submission.sorted_data(
                include=('subject', 'email', 'body', 'please-call-me'),
            ),
            {
                u'Subject': u'Test',
                u'Email': u'valid@example.com',
                u'Body': u'Hello World',
                u'Please call me': False,
            },
        )
