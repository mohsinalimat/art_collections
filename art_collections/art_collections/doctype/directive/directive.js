// Copyright (c) 2022, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Directive', {
	setup: function(frm) {
		frm.set_query('apply_on', () => {
			return {
				filters: {
					name: ['in',['Customer','Customer Group','Supplier','Supplier Group']]
				}
			}
		})
		frm.set_query('apply_for_items', () => {
			return {
				filters: {
					name: ['in',['Item','Item Group']]
				}
			}
		})
		frm.set_query('directive_doctype', 'show_directive_on_doctypes_art', () => {
			return {
				filters: {
					name: ['in',['Quotation','Sales Order','Delivery Note','Sales Invoice','Purchase Receipt','Purchase Invoice','Supplier Quotation','Request For Quotation']]
					// Filter On DocType :  QN,SO,DN,SI,PR,PI,SQ,RFQ
				}
			}
		})				
	}
});
