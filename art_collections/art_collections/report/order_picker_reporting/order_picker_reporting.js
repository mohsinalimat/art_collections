// Copyright (c) 2016, GreyCube Technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Order Picker Reporting"] = {
	"filters": [
		{
			"fieldname":"picker",
			"label": __("Picker"),
			"fieldtype": "Link",
			"options": "User",
			"get_query": function() {
				return {
					query: 'art_collections.pick_list_controller.get_user_with_picker_role',
				}
			}
		},		
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -7),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "60px"
		},
	]
};
