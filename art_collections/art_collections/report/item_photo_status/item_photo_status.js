// Copyright (c) 2016, GreyCube Technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item Photo Status"] = {
	"filters": [		{
		fieldname: "based_on",
		label: __("Based On"),
		fieldtype: "Select",
		options: "< 5 Photo & not resolved\nAll < 5 Photo\nAll Items",
		default: "All Items"
	},

	]
};
