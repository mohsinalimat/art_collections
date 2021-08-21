
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


	}
});