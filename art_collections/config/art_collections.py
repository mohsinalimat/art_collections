from __future__ import unicode_literals
from frappe import _
import frappe


def get_data():
	config = [
		{
			"label": _("Tools"),
			"items": [
				{
					"type": "doctype",
					"name": "Photo Upload Utility",
					"description": _("Utility to Upload Photo to Item and Website slide show.")
				},
				{
					"type": "report",
					"name": "Item Photo Status",
					"is_query_report": True,
					"doctype": "File"
				},
			]
		}
		]
	return config
	