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
		},		{
			"label": _("Documents"),
			"items": [
				{
					"type": "doctype",
					"name": "Catalogue Directory Art",
					"route":"Tree/Catalogue Directory Art" ,
					"description": _("Create Catalogue.")
				}
			]
		}
		]
	return config
	