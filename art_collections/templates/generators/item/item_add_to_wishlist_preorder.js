// function render_wishlist_ui() {
// 		$('.btn-view-in-cart-wishlist').remove()
// 		$('.btn-add-to-cart-wishlist').remove()
// 		var item_code=$("span[itemprop='productID']").text()
// 		frappe.call({
// 			type: "POST",
// 			method: "art_collections.art_cart.get_product_info_for_website",
// 			args: {
// 				item_code: item_code,
// 			},
// 			btn: this,
// 			callback: function(r) {
// 				if (r.message) {
// 					var qty=r.message.wishlist_product_info.qty;
// 					var $button_to_show;
// 					if (qty>0) {
// 						$button_to_show=$('<button class="btn btn-inquiry btn-view-in-cart-wishlist" data-item-code="{{ doc.name }}" data-item-name="{{ doc.item_name }} " > <img class="standard-image" src="/assets/art_collections/images/heart_filled.svg"></button>')
// 					}else{
// 						$button_to_show=$('<button class="btn btn-inquiry btn-add-to-cart-wishlist" data-item-code="{{ doc.name }}" data-item-name="{{ doc.item_name }}"><img class="standard-image" src="/assets/art_collections/images/heart_empty.svg"></button>')
// 					}
// 					$('.div-wishlist').append($button_to_show)
// 				}
// 			}	
// 		});
// 	}
	
	frappe.ready(() => {
console.log("{{ns.wish_list_name_list}}")

		const d = new frappe.ui.Dialog({
			title: __('Wish List'),
			fields: [
				{
					fieldtype: 'Select',
					label: __('Wish List Name'),
					fieldname: 'wish_list_name',
					options:"{{ns.wish_list_name_list}}",
					reqd: 1
				},
				{
				fieldtype: 'Data',
				label: __('item_code'),
				fieldname: 'item_code',
				hidden: 1
			},{
				fieldtype: 'Data',
				label: __('New Wish List Name'),
				fieldname: 'new_wish_list_name',
				hidden: 1
			}
			],
			primary_action: set_wishlist,
			primary_action_label: __('Set')
		});
		function set_wishlist() {
			const values = d.get_values();
			const doc = Object.assign({}, values);
			console.log(doc,values,values.wish_list_name.len)

			d.hide();
			let additional_notes
			let with_items=1
			if(frappe.session.user==="Guest") {
				if(localStorage) {
					localStorage.setItem("last_visited", window.location.pathname);
				}
				window.location.href = "/login";
			} else {
				let additional_notes
				let with_items=1
				if (values.wish_list_name=='create new..') {
					var wish_list_name =values.new_wish_list_name
				}else{
					var wish_list_name = values.wish_list_name
				}		
			return frappe.call({
				type: "POST",
				method: "art_collections.art_cart.update_cart_for_wishlist_preorder",
				args: {
					item_code: values.item_code,
					qty: 1,
					additional_notes: additional_notes !== undefined ? additional_notes : undefined,
					with_items: with_items || 0,
					wish_list_name:wish_list_name
				},
				btn: this,
				callback: function(r) {
					shopping_cart.set_wishlist_cart_count();
					if (r.message.shopping_cart_menu) {
						$('.shopping-cart-menu').html(r.message.shopping_cart_menu);
					}
					location.reload();
					// $btn.prop('disabled', false);
					// render_wishlist_ui() 
				}
			});}
		}
		$('.btn-wishlist-name').on('click', (e) => {
			const $btn = $(e.currentTarget);
			const item_code = $btn.data('item-code');
			console.log(item_code,'item_code')
			const wish_list_name_list= $btn.data('wish_list_name_list');
			// alert(wish_list_name_list)
			d.set_value('new_wish_list_name', '');
			d.set_df_property("new_wish_list_name","hidden",1)
			d.set_df_property("new_wish_list_name","reqd",0)
			d.fields_dict["wish_list_name"].df.onchange = () => {
				var wish_list_name = d.fields_dict.wish_list_name.input.value;
				console.log(wish_list_name)
				if (wish_list_name=='create new..'){
					d.set_df_property("new_wish_list_name","hidden",0)
					d.set_df_property("new_wish_list_name","reqd",1)
				}else{
					d.set_df_property("new_wish_list_name","hidden",1)
					d.set_df_property("new_wish_list_name","reqd",0)				
				}
			}
			d.set_value('item_code', item_code);
			d.show();
		});


		// render_wishlist_ui() 
		// $('.page_content').on('click', '.btn-add-to-cart-wishlist', (e) => {
		// 	const $btn = $(e.currentTarget);
		// 	$btn.prop('disabled', true);
		// 	const item_code = $btn.data('item-code');

		// if(frappe.session.user==="Guest") {
		// 	if(localStorage) {
		// 		localStorage.setItem("last_visited", window.location.pathname);
		// 	}
		// 	window.location.href = "/login";
		// } else {
		// 	let additional_notes
		// 	let with_items=1
		// 	return frappe.call({
		// 		type: "POST",
		// 		method: "art_collections.art_cart.update_cart_for_wishlist_preorder",
		// 		args: {
		// 			item_code: item_code,
		// 			qty: 1,
		// 			additional_notes: additional_notes !== undefined ? additional_notes : undefined,
		// 			with_items: with_items || 0,
		// 			wish_list_name:'Default Wish List'
		// 		},
		// 		btn: this,
		// 		callback: function(r) {
		// 			shopping_cart.set_wishlist_cart_count();
		// 			if (r.message.shopping_cart_menu) {
		// 				$('.shopping-cart-menu').html(r.message.shopping_cart_menu);
		// 			}
		// 			$btn.prop('disabled', false);
		// 			// render_wishlist_ui() 
		// 		}
		// 	});
		// }
		// });
	});
