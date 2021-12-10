frappe.ui.form.on('Website Item', {
	copy_item_specification_art: function (frm) {
		if (frm.doc.item_code) {
			let row1_desc, row2_desc, row3_desc = undefined
			frappe.db.get_value('Item', frm.doc.item_code, ['qty_in_selling_pack_art', 'main_design_color_art', 'length_art', 'width_art', 'thickness_art' ])
				.then(r => {
					let values = r.message;
					if (values.qty_in_selling_pack_art) {
						row1_desc = values.qty_in_selling_pack_art
					}
					if (values.main_design_color_art) {
						row2_desc = values.main_design_color_art
					}
					if (values.length_art) {
						row3_desc = (cstr(values.length_art) || 0) + __('L x ') + (cstr(values.width_art) || 0) + __('W x ') + (cstr(values.thickness_art) || 0) + __('T')
					}
					if (row1_desc) {
						let row1 = frm.add_child('website_specifications')
						row1.label = __('Qty per pack')
						row1.description = '<div class="ql-editor read-mode"><p>'+row1_desc+'</p></div>'
					}
					if (row2_desc) {
						let row2 = frm.add_child('website_specifications')
						row2.label = __('Main Color')
						row2.description ='<div class="ql-editor read-mode"><p>'+row2_desc+'</p></div>' 
					}
					if (row3_desc) {
						let row3 = frm.add_child('website_specifications')
						row3.label = __('Product Dimension')
						row3.description ='<div class="ql-editor read-mode"><p>'+row3_desc+'</p></div>' 
					}
					frm.refresh_field('website_specifications')
				})
		}
	}
});

