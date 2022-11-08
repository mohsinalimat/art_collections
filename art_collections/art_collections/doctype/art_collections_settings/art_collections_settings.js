// Copyright (c) 2021, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Art Collections Settings', {
	setup: function(frm) {
		frm.set_query('saleable_warehouse_group', () => {
			return {
				filters: {
					is_group: 1
				}
			}
		})
		frm.set_query('reserved_warehouse_group', () => {
			return {
				filters: {
					is_group: 1
				}
			}
		})
		frm.set_query('damage_warehouse_group', () => {
			return {
				filters: {
					is_group: 1
				}
			}
		})		
	}
});
