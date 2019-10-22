// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// shopping cart
frappe.provide("erpnext.shopping_cart");
var shopping_cart = erpnext.shopping_cart;

frappe.ready(function() {
	shopping_cart.set_wishlist_cart_count();
	// shopping_cart.wishlist_bind_dropdown_cart_buttons();
});

$.extend(shopping_cart, {

	// show_shoppingcart_dropdown: function() {
	// 	$(".shopping-cart").on('shown.bs.dropdown', function() {
	// 		if (!$('.shopping-cart-menu .cart-container').length) {
	// 			return frappe.call({
	// 				method: 'erpnext.shopping_cart.cart.get_shopping_cart_menu',
	// 				callback: function(r) {
	// 					if (r.message) {
	// 						$('.shopping-cart-menu').html(r.message);
	// 					}
	// 				}
	// 			});
	// 		}
	// 	});
	// },

	// update_cart: function(opts) {
	// 	if(frappe.session.user==="Guest") {
	// 		if(localStorage) {
	// 			localStorage.setItem("last_visited", window.location.pathname);
	// 		}
	// 		window.location.href = "/login";
	// 	} else {
	// 		return frappe.call({
	// 			type: "POST",
	// 			method: "erpnext.shopping_cart.cart.update_cart",
	// 			args: {
	// 				item_code: opts.item_code,
	// 				qty: opts.qty,
	// 				additional_notes: opts.additional_notes !== undefined ? opts.additional_notes : undefined,
	// 				with_items: opts.with_items || 0
	// 			},
	// 			btn: opts.btn,
	// 			callback: function(r) {
	// 				shopping_cart.set_cart_count();
	// 				if (r.message.shopping_cart_menu) {
	// 					$('.shopping-cart-menu').html(r.message.shopping_cart_menu);
	// 				}
	// 				if(opts.callback)
	// 					opts.callback(r);
	// 			}
	// 		});
	// 	}
	// },
	// wishlist_update_cart: function(opts) {
	// 	console.log('opts.additional_notes',opts.additional_notes)
	// 	if(frappe.session.user==="Guest") {
	// 		if(localStorage) {
	// 			localStorage.setItem("last_visited", window.location.pathname);
	// 		}
	// 		window.location.href = "/login";
	// 	} else {
	// 		return frappe.call({
	// 			type: "POST",
	// 			method: "art_collections.art_cart.update_cart_for_wishlist_preorder",
	// 			args: {
	// 				item_code: opts.item_code,
	// 				qty: opts.qty,
	// 				additional_notes: opts.additional_notes !== undefined ? opts.additional_notes : undefined,
	// 				with_items: opts.with_items || 0
	// 			},
	// 			btn: opts.btn,
	// 			callback: function(r) {
	// 				shopping_cart.set_wishlist_cart_count();
	// 				if (r.message.shopping_cart_menu) {
	// 					$('.shopping-cart-menu').html(r.message.shopping_cart_menu);
	// 				}
	// 				if(opts.callback)
	// 					opts.callback(r);
	// 			}
	// 		});
	// 	}
	// },
	// set_cart_count: function() {
	// 	var cart_count = frappe.get_cookie("cart_count");
	// 	if(frappe.session.user==="Guest") {
	// 		cart_count = 0;
	// 	}

	// 	if(cart_count) {
	// 		$(".shopping-cart").toggleClass('hidden', false);
	// 	}

	// 	var $cart = $('.cart-icon');
	// 	var $badge = $cart.find("#cart-count");

	// 	if(parseInt(cart_count) === 0 || cart_count === undefined) {
	// 		$cart.css("display", "none");
	// 		$(".cart-items").html('Cart is Empty');
	// 		$(".cart-tax-items").hide();
	// 		$(".btn-place-order").hide();
	// 		$(".cart-addresses").hide();
	// 	}
	// 	else {
	// 		$cart.css("display", "inline");
	// 	}

	// 	if(cart_count) {
	// 		$badge.html(cart_count);
	// 	} else {
	// 		$badge.remove();
	// 	}
	// },
	set_wishlist_cart_count: function() {
		var wishlist_cart_count = frappe.get_cookie("wishlist_cart_count");
		if(frappe.session.user==="Guest") {
			wishlist_cart_count = 0;
		}

		if(wishlist_cart_count) {
			$(".wishlist-shopping-cart").toggleClass('hidden', false);
		}

		var $cart = $('.wishlist-cart-icon');
		var $badge = $cart.find("#wishlist-cart-count");

		if(parseInt(wishlist_cart_count) === 0 || wishlist_cart_count === undefined) {
			$cart.css("display", "none");
			$(".wishlist-cart-items").html('Cart is Empty');
			$(".cart-tax-items").hide();
			$(".btn-place-order").hide();
			$(".cart-addresses").hide();
		}
		else {
			$cart.css("display", "inline");
		}

		if(wishlist_cart_count) {
			console.log(wishlist_cart_count,$badge,'-----------')
			$badge.html(wishlist_cart_count);
		} else {
			$badge.remove();
		}
	},
	// shopping_cart_update: function({item_code, qty, cart_dropdown, additional_notes}) {
	// 	frappe.freeze();
	// 	shopping_cart.update_cart({
	// 		item_code,
	// 		qty,
	// 		additional_notes,
	// 		with_items: 1,
	// 		btn: this,
	// 		callback: function(r) {
	// 			frappe.unfreeze();
	// 			if(!r.exc) {
	// 				$(".cart-items").html(r.message.items);
	// 				$(".cart-tax-items").html(r.message.taxes);
	// 				if (cart_dropdown != true) {
	// 					$(".cart-icon").hide();
	// 				}
	// 			}
	// 		},
	// 	});
	// },


	// bind_dropdown_cart_buttons: function () {
	// 	console.log('bind_dropdown_cart_buttons')
	// 	$(".cart-icon").on('click', '.number-spinner button', function () {
	// 		var btn = $(this),
	// 			input = btn.closest('.number-spinner').find('input'),
	// 			oldValue = input.val().trim(),
	// 			newVal = 0;

	// 		if (btn.attr('data-dir') == 'up') {
	// 			newVal = parseInt(oldValue) + 1;
	// 		} else {
	// 			if (oldValue > 1) {
	// 				newVal = parseInt(oldValue) - 1;
	// 			}
	// 		}
	// 		input.val(newVal);
	// 		var item_code = input.attr("data-item-code");
	// 		shopping_cart.shopping_cart_update({item_code, qty: newVal, cart_dropdown: true});
	// 		return false;
	// 	});

	// },

	// called from art_cart.js
	wishlist_shopping_cart_update: function({item_code, qty, cart_dropdown, additional_notes}) {
		console.log('wishlist_shopping_cart_update---')
		frappe.freeze();
		shopping_cart.wishlist_update_cart({
			item_code,
			qty,
			additional_notes,
			with_items: 1,
			btn: this,
			callback: function(r) {
				frappe.unfreeze();
				if(!r.exc) {
					$(".wishlist-cart-items").html(r.message.items);
					$(".cart-tax-items").html(r.message.taxes);
					if (cart_dropdown != true) {
						$(".wishlist-cart-icon").hide();
					}
				}
			},
		});
	},


	// wishlist_bind_dropdown_cart_buttons: function () {
	// 	console.log('wishlist_bind_dropdown_cart_buttons')
	// 	$(".wishlist-cart-icon").on('click', '.number-spinner button', function () {
	// 		var btn = $(this),
	// 			input = btn.closest('.number-spinner').find('input'),
	// 			oldValue = input.val().trim(),
	// 			newVal = 0;

	// 		if (btn.attr('data-dir') == 'up') {
	// 			newVal = parseInt(oldValue) + 1;
	// 		} else {
	// 			if (oldValue > 1) {
	// 				newVal = parseInt(oldValue) - 1;
	// 			}
	// 		}
	// 		input.val(newVal);
	// 		var item_code = input.attr("data-item-code");
	// 		shopping_cart.wishlist_shopping_cart_update({item_code, qty: newVal, cart_dropdown: true});
	// 		return false;
	// 	});

	// },	

});
