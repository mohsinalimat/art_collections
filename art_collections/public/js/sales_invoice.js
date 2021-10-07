frappe.ui.form.on('Sales Invoice', {
	filter_bank_account:function(frm){
		frm.set_query('bank_account_art', () => {
			return {
					filters: {
							party_type: 'Customer',
							party:frm.doc.customer
					}
			}
	})	
	},
	customer: function (frm) {
		if (frm.doc.customer && frm.doc.payment_method_art==__('Traite') ) {
				frm.trigger('filter_bank_account')
		}
	},
	payment_method_art: function (frm) {
		if (frm.doc.customer && frm.doc.payment_method_art==__('Traite')) {
				frm.trigger('filter_bank_account')
		}
	}	
})