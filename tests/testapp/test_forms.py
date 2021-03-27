from django import forms
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from feincms.module.page.models import Page

from form_designer.models import FIELD_TYPES, Form, FormSubmission


def validate_honeypot(form, data, **kwargs):
    if data.get("honeypot"):
        raise forms.ValidationError("Hello honeypot")


Form.CONFIG_OPTIONS.append(
    ("honeypot", {"title": "Honeypot", "validate": validate_honeypot})
)


class FormsTest(TestCase):
    def test_forms(self):
        form = Form.objects.create(
            title="Test contact form",
            config_json=('{"email": {"email": "info@example.com"}, "save_fs": {}}'),
        )
        form.fields.create(ordering=0, title="Subject", name="subject", type="text")
        form.fields.create(ordering=1, title="Email", name="email", type="email")
        form.fields.create(ordering=2, title="Body", name="body", type="longtext")
        form.fields.create(
            ordering=3,
            title="Please call me",
            name="please-call-me",
            type="checkbox",
            is_required=False,
        )

        form_class = form.form_class()
        form_instance = form_class()

        self.assertListEqual(
            [field.name for field in form_instance],
            ["subject", "email", "body", "please-call-me"],
        )

        page = Page.objects.create(override_url="/", title="")
        page.formcontent_set.create(
            region="main",
            ordering=0,
            form=form,
            success_message="Thanks, we will get back to you",
        )

        response = self.client.get("/")

        self.assertContains(response, 'method="post"', 1)
        self.assertContains(response, 'action="#form{0}"'.format(form.id), 1)
        self.assertContains(
            response,
            "<input",
            6,  # csrf, subject, email, checkbox, _formcontent, submit
        )
        self.assertContains(response, "<textarea", 1)

        response = self.client.post("/")

        self.assertContains(response, "This field is required", 3)

        # Not this form
        response = self.client.post("/", {"_formcontent": -1})

        self.assertNotContains(response, "This field is required")

        response = self.client.post(
            "/",
            {
                "_formcontent": form.id,
                "fc{0}-subject".format(form.id): "Test",
                "fc{0}-email".format(form.id): "invalid",
                "fc{0}-body".format(form.id): "Hello World",
            },
        )

        self.assertNotContains(response, "This field is required")

        self.assertContains(
            response, "Enter a valid e", 1  # Django 1.4 has e-mail, 1.5 and up email
        )

        response = self.client.post(
            "/",
            {
                "_formcontent": form.id,
                "fc{0}-subject".format(form.id): "Test",
                "fc{0}-email".format(form.id): "valid@example.com",
                "fc{0}-body".format(form.id): "Hello World",
            },
        )

        self.assertContains(response, "Thanks, we will get back to you", 1)

        self.assertNotContains(response, "<form")

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]

        self.assertListEqual(message.to, ["info@example.com"])
        self.assertEqual(message.from_email, "no-reply@example.com")
        self.assertEqual(message.subject, "Test contact form")
        self.assertIn("subject: Test\n", message.body)
        self.assertIn("email: valid@example.com\n", message.body)
        self.assertIn("body: Hello World\n", message.body)
        self.assertIn("please-call-me: False\n", message.body)

        # Exactly one submission
        submission = FormSubmission.objects.get()

        self.assertEqual(
            submission.sorted_data(
                include=("subject", "email", "body", "please-call-me")
            ),
            {
                "subject": "Test",
                "email": "valid@example.com",
                "body": "Hello World",
                "please-call-me": False,
            },
        )

        # Export the submission
        User.objects.create_superuser("admin", "admin@example.com", "password")
        self.client.login(username="admin", password="password")
        response = self.client.get(
            "/admin/form_designer/form/{}/export_submissions/".format(
                submission.form_id
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        response = self.client.get(
            "/admin/form_designer/formsubmission/{}/change/".format(submission.id)
        )
        self.assertContains(response, "<dt>body</dt>")

    def test_admin(self):
        User.objects.create_superuser("admin", "admin@example.com", "password")
        self.client.login(username="admin", password="password")

        response = self.client.get("/admin/form_designer/form/add/")
        self.assertEqual(response.status_code, 200)  # Oh well...

        data = {
            "title": "Test form",
            # "config_json": '{"save_fs": {}}',
            "_is_active_save_fs": "on",
            "_is_active_email": "on",
            "email_email": "bla@example.com,blabbb@example.com",
            "fields-TOTAL_FORMS": 7,
            "fields-INITIAL_FORMS": 0,
            "fields-MIN_NUM_FORMS": 0,
            "fields-MAX_NUM_FORMS": 1000,
        }
        for i in range(7):
            data["fields-{}-ordering".format(i)] = (i + 1) * 10
            data["fields-{}-title".format(i)] = "title-{}".format(i)
            data["fields-{}-name".format(i)] = "name-{}".format(i)
            data["fields-{}-type".format(i)] = FIELD_TYPES[i]["type"]
            data["fields-{}-choices".format(i)] = ""

        # Validation failure because of missing choices
        response = self.client.post("/admin/form_designer/form/add/", data)
        self.assertEqual(response.status_code, 200)

        for i in range(7):
            if FIELD_TYPES[i]["type"] in {"select", "radio", "multiple-select"}:
                data["fields-{}-choices".format(i)] = "a,b,c,d"

        data["fields-0-choices"] = "invalid"
        # Validation failure because of choices where there should be none
        response = self.client.post("/admin/form_designer/form/add/", data)
        self.assertEqual(response.status_code, 200)

        data["fields-0-choices"] = ""
        response = self.client.post("/admin/form_designer/form/add/", data)
        self.assertRedirects(response, "/admin/form_designer/form/")

        data["fields-4-type"] = ""  # No crash, but no success either
        response = self.client.post("/admin/form_designer/form/add/", data)
        self.assertEqual(response.status_code, 200)

        # Basic smoke test
        form = Form.objects.get()
        self.assertEqual(set(form.config), {"email", "save_fs"})
        form_class = form.form_class()

        self.assertEqual(form.title, "Test form")
        self.assertEqual(len(form_class().fields), 7)

        # The additional formsets exist
        response = self.client.get(
            "/admin/form_designer/form/{}/change/".format(form.id)
        )
        self.assertContains(response, 'id="id_email_email"')
        self.assertContains(response, "blabbb@example.com")

    def test_honeypot(self):
        form = Form.objects.create(
            title="Test honeypot form",
            config_json=('{"honeypot": {}}'),
        )
        form.fields.create(ordering=0, title="Subject", name="subject", type="text")
        form.fields.create(
            ordering=0,
            title="honeypot",
            name="honeypot",
            type="hidden",
            is_required=False,
        )

        page = Page.objects.create(override_url="/", title="")
        page.formcontent_set.create(
            region="main",
            ordering=0,
            form=form,
            success_message="Thanks, we will get back to you",
        )

        response = self.client.post(
            "/",
            {
                "_formcontent": form.id,
                "fc{0}-subject".format(form.id): "Test",
                "fc{0}-honeypot".format(form.id): "honey",
            },
        )

        self.assertContains(response, "Hello honeypot")
