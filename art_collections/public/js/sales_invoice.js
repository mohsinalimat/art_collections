frappe.ui.form.on('Sales Invoice', {
	// onload_post_render: function (frm) {
	// 	frappe.call('art_collections.item_controller.get_all_saleable_warehouse_list')
	// 		.then(saleable_warehouse_type => {
	// 			if (saleable_warehouse_type) {
	// 				frm.set_query('warehouse', 'items', () => {
	// 					return {
	// 						filters: {
	// 							warehouse_type: ['in', saleable_warehouse_type.message]
	// 						}
	// 					}
	// 				})
	// 			}
	// 		})
	// },

	refresh: function (frm) {
		// frappe.add_product_excel_button(frm, "art_collections.controllers.excel.sales_invoice_excel._make_excel_attachment")

	},


	customer: function (frm) {
		if (frm.doc.customer && frm.doc.mode_of_payment_art != undefined && (frm.doc.mode_of_payment_art == __('Traite') || frm.doc.mode_of_payment_art.indexOf(__('LCR')) == 0)) {
			set_bank_account_for_customer(frm.doc.customer, frm.doc.shipping_address_name, frm)
		}
	},
	mode_of_payment_art: function (frm) {
		if ((frm.doc.customer || frm.doc.shipping_address_name && frm.doc.mode_of_payment_art != undefined && frm.doc.mode_of_payment_art == __('Traite') || frm.doc.mode_of_payment_art.indexOf(__('LCR')) == 0)) {
			set_bank_account_for_customer(frm.doc.customer, frm.doc.shipping_address_name, frm)
		}
	},
	shipping_address_name: function (frm) {
		if (frm.doc.shipping_address_name && frm.doc.mode_of_payment_art != undefined && (frm.doc.mode_of_payment_art == __('Traite') || frm.doc.mode_of_payment_art.indexOf(__('LCR')) == 0)) {
			set_bank_account_for_customer(frm.doc.customer, frm.doc.shipping_address_name, frm)
		}
	}
})

function set_bank_account_for_customer(customer, shipping_address, frm) {
	frappe.call({
		method: 'art_collections.sales_invoice_controller.set_bank_account_for_customer',
		args: {
			customer: customer || undefined,
			shipping_address: shipping_address || undefined
		},
		callback: (r) => {
			if (r && r.message) {
				frm.set_value('bank_account_art', r.message)

			} else {
				filter_bank_account(frm)
			}

		}
	})
}

function filter_bank_account(frm) {
	frm.set_query('bank_account_art', () => {
		return {
			filters: {
				party_type: 'Customer',
				party: frm.doc.customer
			}
		}
	})
}