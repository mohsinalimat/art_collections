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
	],
};

function toggle_allow_insufficient_images(docname) {
	let checked = document.getElementById(docname).checked;
	if (checked == false) {
		checked = 0
	} else if (checked == true) {
		checked = 1
	}
	return frappe.db.set_value('Item', docname, 'allow_insufficient_images_for_web_art', checked,
		function (r) {
			if (!r.exc) {
				frappe.query_report.refresh();
			} else {
				frappe.msgprint(r.exc);
			}
		}
	)
}
