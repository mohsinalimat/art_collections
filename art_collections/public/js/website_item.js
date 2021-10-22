frappe.ui.form.on('Website Item', {
	copy_item_specification_art: function (frm) {
		if (frm.doc.item_code) {
			let row1_desc, row2_desc, row3_desc = undefined
			frappe.db.get_value('Item', frm.doc.item_code, ['qty_in_selling_pack_art', 'main_design_color_art', 'length_art', 'width_art', 'thickness_art', 'item_group', ])
				.then(r => {
					let values = r.message;
					if (values.qty_in_selling_pack_art) {
						row1_desc = values.qty_in_selling_pack_art + __(' qty per pack for this item in ') + values.item_group + __(' group')
					}
					if (values.main_design_color_art) {
						row2_desc = values.main_design_color_art + __(' is the main color')
					}
					if (values.length_art) {
						row3_desc = (values.length_art || 0) + __('L x ') + (values.width_art || 0) + __('W x ') + (values.thickness_art || 0) + __('T')
					}
					if (row1_desc) {
						let row1 = frm.add_child('website_specifications')
						row1.label = __('Qty per pack')
						row1.description = row1_desc
					}
					if (row2_desc) {
						let row2 = frm.add_child('website_specifications')
						row2.label = __('Main Color')
						row2.description = row2_desc
					}
					if (row3_desc) {
						let row3 = frm.add_child('website_specifications')
						row3.label = __('Product Dimension')
						row3.description = row3_desc
					}
					frm.refresh_field('website_specifications')
				})
		}
	}
});