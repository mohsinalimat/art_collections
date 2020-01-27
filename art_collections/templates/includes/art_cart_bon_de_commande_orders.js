// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// js inside blog page

// shopping cart
frappe.provide("erpnext.shopping_cart");
var shopping_cart = erpnext.shopping_cart;

$.extend(shopping_cart, {
	bind_events: function() {
		shopping_cart.bind_place_bon_de_commande_order();
	},
	bind_place_bon_de_commande_order: function() {
		$(".btn-place-bon-de-commande-order").on("click", function() {
			shopping_cart.place_bon_de_commande_order(this);
		});
	},
	place_bon_de_commande_order: function(btn) {
		return frappe.call({
			type: "POST",
			method: "art_collections.art_cart.place_bon_de_commande_order",
			btn: btn,
			callback: function(r) {
				if(r.exc) {
					var msg = "";
					if(r._server_messages) {
						msg = JSON.parse(r._server_messages || []).join("<br>");
					}

					$("#cart-error")
						.empty()
						.html(msg || frappe._("Something went wrong!"))
						.toggle(true);
				} else {
					$('.cart-container table').hide();
					$(btn).hide();
					window.location.href = '/orders/' + encodeURIComponent(r.message);
				}
			}
		});
	}
});

frappe.ready(function() {
	shopping_cart.bind_events();
});
