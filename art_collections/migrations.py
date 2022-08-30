import frappe
from frappe.modules.import_file import import_file_by_path
from frappe.utils import get_bench_path
import os
from os.path import join


def after_migrations():
    update_dashboard_link_for_core_doctype(
        "Customer", "Directive", "apply_for_value", "Directive"
    )
    update_dashboard_link_for_core_doctype(
        "Customer Group", "Directive", "apply_for_value", "Directive"
    )
    update_dashboard_link_for_core_doctype(
        "Supplier", "Directive", "apply_for_value", "Directive"
    )
    update_dashboard_link_for_core_doctype(
        "Supplier Group", "Directive", "apply_for_value", "Directive"
    )

    update_dashboard_link_for_core_doctype(
        "Item", "Directive", "apply_for_item_value", "Directive"
    )
    update_dashboard_link_for_core_doctype(
        "Item Group", "Directive", "apply_for_item_value", "Directive"
    )

    # if(not frappe.db.exists('Notification','validate_inner_qty_for_sales_order')):
    fname = "notification.json"
    import_folder_path = "{bench_path}/{app_folder_path}".format(
        bench_path=get_bench_path(),
        app_folder_path="/apps/art_collections/art_collections/import_records",
    )
    make_records(import_folder_path, fname)

    if not frappe.db.exists("Property Setter", "Sales Order-delivery_date-no_copy"):
        fname = "property_setter.json"
        import_folder_path = "{bench_path}/{app_folder_path}".format(
            bench_path=get_bench_path(),
            app_folder_path="/apps/art_collections/art_collections/import_records",
        )
        make_records(import_folder_path, fname)

    add_fixtures()


def make_records(path, fname):
    if os.path.isdir(path):
        import_file_by_path("{path}/{fname}".format(path=path, fname=fname))


def update_dashboard_link_for_core_doctype(
    doctype, link_doctype, link_fieldname, group=None
):
    try:
        d = frappe.get_doc("Customize Form")
        if doctype:
            d.doc_type = doctype
        d.run_method("fetch_to_customize")
        for link in d.get("links"):
            if (
                link.link_doctype == link_doctype
                and link.link_fieldname == link_fieldname
            ):
                # found so just return
                return
        d.append(
            "links",
            dict(
                link_doctype=link_doctype,
                link_fieldname=link_fieldname,
                table_fieldname=None,
                group=group,
            ),
        )
        d.run_method("save_customization")
        frappe.clear_cache()
    except Exception:
        frappe.log_error(frappe.get_traceback())


def add_fixtures():
    # create print format for Sales Order
    records = [
        {
            "doctype": "Print Format",
            "name": "Art Collections Sales Order",
            "docstatus": 0,
            "idx": 0,
            "module": "Art Collections",
            "disabled": 0,
            "custom_format": 1,
            "font": "Default",
            "html": '<div>{% include "templates/includes/art_collections_sales_order.html" %}</div>',
            "css": "",
            "print_format_builder": 0,
            "standard": "No",
            "align_labels_right": 0,
            "print_format_type": "Jinja",
            "doc_type": "Sales Order",
            "default_print_language": "en",
            "show_section_headings": 0,
        }
    ]

    if not frappe.db.exists("Email Template", "Welcome Email Art"):
        print("adding welcome email art, email template")
        records = records + [
            {
                "doctype": "Email Template",
                "name": "Welcome Email Art",
                "response": """
                        {% set site_link = "<a href='" + site_url + "'>" + site_url + "</a>" %}
                        <p>{{_("Hello")}} {{ first_name }}{% if last_name %} {{ last_name}}{% endif %},</p>
                        <p> This is a custom welcome message set from Email Template <br></p>
                        <p>{{_("A new account has been created for you at {0}").format(site_link)}}.</p>
                        <p>{{_("Your login id is")}}: <b>{{ user }}</b></p>
                        <p>{{_("Click on the link below to complete your registration and set a new password")}}.</p>
                        <p><a href="{{ link }}" rel="nofollow" class="btn btn-primary">{{ _("Complete Registration") }}</a></p>
                        {% if created_by != "Administrator" %}
                        <p>{{_("Thanks")}},<br></p>
                        <p>{{ created_by }}</p>
                        {% endif %}
                        <p>{{_("You can also copy-paste following link in your browser")}}<br></p>
                        <p><a href="{{ link }}">{{ link }}</a></p>
                """,
                "subject": " Welcome to Artifêtes Diffusion",
                "use_html": 0,
                "owner": "Administrator",
            }
        ]

    from frappe.desk.page.setup_wizard.setup_wizard import make_records as _make_records

    _make_records(records)
