	function render_wishlist_ui() {
		$('.btn-view-in-cart-wishlist').remove()
		$('.btn-add-to-cart-wishlist').remove()
		var item_code=$("span[itemprop='productID']").text()
		frappe.call({
			type: "POST",
			method: "art_collections.art_cart.get_product_info_for_website",
			args: {
				item_code: item_code,
			},
			btn: this,
			callback: function(r) {
				if (r.message) {
					var qty=r.message.wishlist_product_info.qty;
					var $button_to_show;
					if (qty>0) {
						$button_to_show=$('<button class="btn btn-inquiry btn-view-in-cart-wishlist" data-item-code="{{ doc.name }}" data-item-name="{{ doc.item_name }} " > <img class="standard-image" src="/assets/art_collections/images/heart_filled.svg"></button>')
					}else{
						$button_to_show=$('<button class="btn btn-inquiry btn-add-to-cart-wishlist" data-item-code="{{ doc.name }}" data-item-name="{{ doc.item_name }}"><img class="standard-image" src="/assets/art_collections/images/heart_empty.svg"></button>')
					}
					$('.div-wishlist').append($button_to_show)
				}
			}	
		});
	}
	
	frappe.ready(() => {
		render_wishlist_ui() 
		$('.page_content').on('click', '.btn-add-to-cart-wishlist', (e) => {
			const $btn = $(e.currentTarget);
			$btn.prop('disabled', true);
			const item_code = $btn.data('item-code');

		if(frappe.session.user==="Guest") {
			if(localStorage) {
				localStorage.setItem("last_visited", window.location.pathname);
			}
			window.location.href = "/login";
		} else {
			let additional_notes
			let with_items=1
			return frappe.call({
				type: "POST",
				method: "art_collections.art_cart.update_cart_for_wishlist_preorder",
				args: {
					item_code: item_code,
					qty: 1,
					additional_notes: additional_notes !== undefined ? additional_notes : undefined,
					with_items: with_items || 0
				},
				btn: this,
				callback: function(r) {
					shopping_cart.set_wishlist_cart_count();
					if (r.message.shopping_cart_menu) {
						$('.shopping-cart-menu').html(r.message.shopping_cart_menu);
					}
					$btn.prop('disabled', false);
					render_wishlist_ui() 
				}
			});
		}
		});
	});
