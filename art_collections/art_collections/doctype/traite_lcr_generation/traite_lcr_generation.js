// Copyright (c) 2022, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Traite LCR Generation', {
	generate_file: function (frm) {
		return frappe.call({
			method: "generate_traite_lcr",
			doc: frm.doc,
			callback: function (r, rt) {
				frm.reload_doc();
			}
		});
	},

	setup: function (frm) {
		frm.set_query('company_bank_account', () => {
			return {
				filters: {
					is_company_account: 1
				}
			}
		})
	}
});
