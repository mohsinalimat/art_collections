frappe.ui.form.on('Website Item', {
	onload:function (frm) {
		frm.set_query('catalogue', 'catalogue_directory_art_website_cf', () => {
		   return {
			   filters: {
				   'node_type': 'Catalogue'
			   }
		   }
	   })
	   frm.set_query('universe', 'catalogue_directory_art_website_cf', (frm,cdt,cdn) => {
		let row=locals[cdt][cdn]
		return {
			filters: {
				'parent_catalogue_directory_art': row.catalogue
			}
		}
	})     
	 },	
	copy_catalogue_item_cf:function (frm) {
		frappe.call('art_collections.art_collections.doctype.catalogue_directory_art.catalogue_directory_art.get_universe_items_from_catalogue_directory_art', {
			item_name: frm.doc.item_code
		}).then(r => {
			console.log(r.message)
			let catalogue_directory_art_list=r.message
			if (catalogue_directory_art_list) {
				for (let index = 0; index < catalogue_directory_art_list.length; index++) {
					let catalogue=catalogue_directory_art_list[index].catalogue
					let universe=catalogue_directory_art_list[index].universe
					let catalogue_directory_art_website_cf=frm.doc.catalogue_directory_art_website_cf
					let found_existing=false
					for (let index = 0; index < catalogue_directory_art_website_cf.length; index++) {
						let existing_catalogue= catalogue_directory_art_website_cf[index].catalogue;
						let existing_universe=catalogue_directory_art_website_cf[index].universe
						if (existing_catalogue==catalogue && existing_universe==universe) {
							found_existing=true
							break
						}
					}
					if (found_existing==false) {
						let row=frm.add_child('catalogue_directory_art_website_cf')
						row.catalogue=catalogue
						row.universe=universe
						frm.refresh_field('catalogue_directory_art_website_cf')
					}	
				}				
			}
		})		
	},
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

