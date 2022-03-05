frappe.ui.form.on('Sales Invoice', {
	onload_post_render: function (frm) {
		frappe.call('art_collections.item_controller.get_all_saleable_warehouse_list')
			.then(saleable_warehouse_type => {
				if (saleable_warehouse_type) {
					frm.set_query('warehouse', 'items', () => {
						return {
							filters: {
								warehouse_type: ['in', saleable_warehouse_type.message]
							}
						}
					})
				}
			})
	},
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
		if (frm.doc.customer && frm.doc.mode_of_payment_art==__('Traite') ) {
				frm.trigger('filter_bank_account')
		}
	},
	mode_of_payment_art: function (frm) {
		if (frm.doc.customer && frm.doc.mode_of_payment_art==__('Traite')) {
				frm.trigger('filter_bank_account')
		}
	}	
})