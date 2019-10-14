	frappe.ready(() => {
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
			console.log('rrrrrrrr')
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
					console.log('rrrrrrrr',r.message)
					// shopping_cart.set_cart_count();
					if (r.message.shopping_cart_menu) {
						$('.shopping-cart-menu').html(r.message.shopping_cart_menu);
					}
					$btn.prop('disabled', false);
					// $('.btn-add-to-cart-wishlist').find('i').toggleClass('fa-heart-o fa-heart');
					$('.btn-add-to-cart-wishlist, .btn-view-in-cart-wishlist').toggleClass('hidden');

				}
			});
		}
		});
	});
