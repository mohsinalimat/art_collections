frappe.ui.form.on('Sales Invoice', {
	onload_post_render: function (frm) {
		frappe.db.get_value('Art Collections Settings', 'Art Collections Settings', ['saleable_warehouse_type', 'reserved_warehouse_type'])
			.then(r => {
				let saleable_warehouse_type = r.message.saleable_warehouse_type
				let reserved_warehouse_type = r.message.reserved_warehouse_type
				if (saleable_warehouse_type || reserved_warehouse_type) {
					if (saleable_warehouse_type != null && reserved_warehouse_type != null) {
						frm.set_query('warehouse', 'items', () => {
							return {
								filters: {
									warehouse_type: ['in', [saleable_warehouse_type, reserved_warehouse_type]]
								}
							}
						})
					} else if (saleable_warehouse_type != null && reserved_warehouse_type == null) {
						frm.set_query('warehouse', 'items', () => {
							return {
								filters: {
									warehouse_type: ['=', saleable_warehouse_type]
								}
							}
						})
					} else if (saleable_warehouse_type == null && reserved_warehouse_type != null) {
						frm.set_query('warehouse', 'items', () => {
							return {
								filters: {
									warehouse_type: ['=', reserved_warehouse_type]
								}
							}
						})
					}
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