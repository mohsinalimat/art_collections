import frappe
from frappe.modules.import_file import import_file_by_path
from frappe.utils import get_bench_path
import os
from os.path import join


def after_migrations():
	update_dashboard_link_for_core_doctype(doctype='Supplier',link_doctype='Supplier Item Directive',link_fieldname='supplier')
	if(not frappe.db.exists('Workflow','BDC')):
		fname="workflow.json"
		import_folder_path="{bench_path}/{app_folder_path}".format(bench_path=get_bench_path(),app_folder_path='/apps/art_collections/art_collections/import_records')
		make_records(import_folder_path,fname)

	# if(not frappe.db.exists('Notification','validate_inner_qty_for_sales_order')):
	fname="notification.json"
	import_folder_path="{bench_path}/{app_folder_path}".format(bench_path=get_bench_path(),app_folder_path='/apps/art_collections/art_collections/import_records')
	make_records(import_folder_path,fname)

	if(not frappe.db.exists('Property Setter','Sales Order-delivery_date-no_copy')):
		fname="property_setter.json"
		import_folder_path="{bench_path}/{app_folder_path}".format(bench_path=get_bench_path(),app_folder_path='/apps/art_collections/art_collections/import_records')
		make_records(import_folder_path,fname)


def make_records(path, fname):
	if os.path.isdir(path):
		import_file_by_path("{path}/{fname}".format(path=path, fname=fname))


def update_dashboard_link_for_core_doctype(doctype,link_doctype,link_fieldname,group=None):
	try:
		d = frappe.get_doc("Customize Form")
		if doctype:
			d.doc_type = doctype
		d.run_method("fetch_to_customize")
		for link in d.get('links'):
			if link.link_doctype==link_doctype and link.link_fieldname==link_fieldname:
				# found so just return
				return
		d.append('links', dict(link_doctype=link_doctype, link_fieldname=link_fieldname,table_fieldname=None,group=group))
		d.run_method("save_customization")
		frappe.clear_cache()
	except Exception:
		frappe.log_error(frappe.get_traceback())
