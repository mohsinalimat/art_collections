// Copyright (c) 2022, GreyCube Technologies and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Container Followup"] = {
	"filters": [

	],


	"formatter": function (value, row, column, data, default_formatter) {

		value = default_formatter(value, row, column, data);
		if (column.id == 'spl_name') {
			value = linkify('supplier-packing-list-art', value)
		} else if (column.id == 'supplier') {
			value = linkify('supplier', value)
		} else if (column.id == 'po_name') {
			value = linkify('purchase-order', value)
		} else if (column.id == 'pr_name') {
			value = linkify('purchase-receipt', value)
		} else if (column.id == 'pr_shipping_address') {
			value = linkify('address', value)
		}
		return value;
	},


};


function linkify(doctype, value) {
	let links = value.split(",").map((d) => {
		return `<a href="/app/${doctype}/${d.split(":")[0]}">${d}</a>`
	})
	return links.join(",")
}