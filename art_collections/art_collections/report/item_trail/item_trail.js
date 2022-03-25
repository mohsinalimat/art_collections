// Copyright (c) 2022, GreyCube Technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item Trail"] = {
	"filters": [{
		"fieldname": "to_date",
		"label": __("On Date"),
		"fieldtype": "Date",
		"default": frappe.datetime.get_today(),
		"reqd": 1,
		"width": "60px"
	},],
	//  make link field for comma seperated cell data ex. cust1,cust2
	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname == "best_customer") {
			let links = value.split(",").map((d) => {
				return `<a href="/app/customer/${d}">${d}</a>`
			})
			let link_value = links.join(",")
			return link_value;
		}
		if (column.fieldname == "supplier") {
			let links = value.split(",").map((d) => {
				return `<a href="/app/supplier/${d}">${d}</a>`
			})
			let link_value = links.join(",")
			return link_value;
		}		
		// for other normal cols
		return value;
	},
};