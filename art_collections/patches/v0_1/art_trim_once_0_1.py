import frappe
from frappe.model import (
		data_fieldtypes,
		default_fields,
		no_value_fields,
		optional_fields,
		table_fields,
	)

def execute():
	art_trim_tables()
	# frappe.model.meta.trim_tables()


def art_trim_tables(doctype=None):
	ignore_fields = default_fields + optional_fields

	filters = {"issingle": 0, "name": ["not in", ["test","DocType"]]}
	if doctype:
		filters["name"] = doctype

	for doctype in frappe.db.get_all("DocType", filters=filters):
		doctype = doctype.name
		columns = frappe.db.get_table_columns(doctype)
		fields = frappe.get_meta(doctype).get_fieldnames_with_value()
		columns_to_remove = [
			f for f in list(set(columns) - set(fields)) if f not in ignore_fields and not f.startswith("_")
		]
		if columns_to_remove:
			print(doctype, "columns removed:", columns_to_remove)
			columns_to_remove = ", ".join(["drop `{0}`".format(c) for c in columns_to_remove])
			query = """alter table `tab{doctype}` {columns}""".format(
				doctype=doctype, columns=columns_to_remove
			)
			frappe.db.sql_ddl(query)