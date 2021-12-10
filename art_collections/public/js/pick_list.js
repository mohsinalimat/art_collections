frappe.ui.form.on('Pick List', {
	setup: (frm) => {
		frappe.db.get_single_value('Art Collections Settings', 'picker_role')
			.then(picker_role => {
				console.log(picker_role);
				if (picker_role) {
					frm.set_query('picker_responsible_art', () => {
						return {
							query: 'art_collections.pick_list_controller.get_user_with_picker_role',
						};
					});
				}
			})
	},
	onload_post_render: function (frm) {
		frappe.db.get_value('Art Collections Settings', 'Art Collections Settings', ['saleable_warehouse_type', 'reserved_warehouse_type'])
			.then(r => {
				let saleable_warehouse_type = r.message.saleable_warehouse_type
				let reserved_warehouse_type = r.message.reserved_warehouse_type
				if (saleable_warehouse_type || reserved_warehouse_type) {
					if (saleable_warehouse_type != null && reserved_warehouse_type != null) {
						frm.set_query('parent_warehouse', () => {
							return {
								filters: {
									warehouse_type: ['in', [saleable_warehouse_type, reserved_warehouse_type]]
								}
							}
						})
					} else if (saleable_warehouse_type != null && reserved_warehouse_type == null) {
						frm.set_query('parent_warehouse', () => {
							return {
								filters: {
									warehouse_type: ['=', saleable_warehouse_type]
								}
							}
						})
					} else if (saleable_warehouse_type == null && reserved_warehouse_type != null) {
						frm.set_query('parent_warehouse', () => {
							return {
								filters: {
									warehouse_type: ['=', saleable_warehouse_type]
								}
							}
						})
					}
				}
			})
	}
});