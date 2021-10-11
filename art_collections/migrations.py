import frappe
from frappe.modules.import_file import import_file_by_path
from frappe.utils import get_bench_path
import os
from os.path import join


def after_migrations():
	if(not frappe.db.exists('Workflow','BDC')):
		fname="workflow.json"
		import_folder_path="{bench_path}/{app_folder_path}".format(bench_path=get_bench_path(),app_folder_path='/apps/art_collections/art_collections/import_records')
		make_records(import_folder_path,fname)

	if(not frappe.db.exists('Notification','validate_inner_qty_for_sales_order')):
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