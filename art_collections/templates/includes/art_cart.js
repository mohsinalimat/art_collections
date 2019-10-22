// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// js inside blog page

// shopping cart
frappe.provide("erpnext.shopping_cart");
var shopping_cart = erpnext.shopping_cart;

$.extend(shopping_cart, {
	bind_events: function() {
		shopping_cart.wishlist_bind_change_qty();
		shopping_cart.wishlist_bind_change_notes();
	},

	wishlist_bind_change_qty: function() {
		// bind update button
		$(".wishlist-cart-items").on("change", ".cart-qty", function() {
			var item_code = $(this).attr("data-item-code");
			var newVal = $(this).val();
			var btn = $(this)
			var additional_notes=btn.data('additional-notes');
			shopping_cart.wishlist_shopping_cart_update({item_code, qty: newVal,additional_notes: additional_notes});
		});

		$(".wishlist-cart-items").on('click', '.number-spinner button', function () {
			var btn = $(this),
				input = btn.closest('.number-spinner').find('input'),
				oldValue = input.val().trim(),
				newVal = 0;

			if (btn.attr('data-dir') == 'up') {
				newVal = parseInt(oldValue) + 1;
			} else {
				if (oldValue > 1) {
					newVal = parseInt(oldValue) - 1;
				}	
			}
			input.val(newVal);
			var additional_notes=btn.data('additional-notes');
			var item_code = input.attr("data-item-code");
			shopping_cart.wishlist_shopping_cart_update({item_code, qty: newVal,additional_notes: additional_notes});
		});
	},

	wishlist_bind_change_notes: function() {
		$('.wishlist-cart-items').on('change', 'textarea', function() {
			const $textarea = $(this);
			const item_code = $textarea.attr('data-item-code');
			const qty = $textarea.closest('tr').find('.cart-qty').val();
			const notes = $textarea.val();
			shopping_cart.wishlist_shopping_cart_update({
				item_code,
				qty,
				additional_notes: notes
			});
		});
	},


});

frappe.ready(function() {
	$(".wishlist-shopping-cart").hide();
	shopping_cart.bind_events();
});
