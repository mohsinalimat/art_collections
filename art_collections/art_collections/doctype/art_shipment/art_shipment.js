frappe.ui.form.on('Art Shipment', {
	refresh: function (frm) {
		$('div').find('.document-link[data-doctype="Purchase Order"]').remove();
		if (frm.is_new() == undefined) {

			frappe.call('art_collections.art_collections.doctype.art_shipment.art_shipment.get_connected_purchase_order', {
				art_shipment: frm.doc.name
			}).then(r => {
				console.log(r,'r')
				if (r.message && r.message != undefined) {
					let count=r.message.length
					let link = $(`
			<div class="document-link" data-doctype="Purchase Order">
				<div class="document-link-badge" data-doctype="Purchase Order"> <span class="count">${count}</span> <a
					class="badge-link">Purchase Order</a> </div> <span class="open-notification hidden"
				title="Open Purchase Order"> </span></div>
			`);

					link.on('click', function () {
						frappe.route_options = {
							'name': ['in', r.message]
						};
						frappe.set_route("List", "Purchase Order", "List");

					})
					$('div').find('.document-link[data-doctype="Supplier Packing List Art"]').after(link);
				}
			})
		}
	
		$('div').find('.document-link[data-doctype="Purchase Receipt"]').remove();
		if (frm.is_new() == undefined) {

			frappe.call('art_collections.art_collections.doctype.art_shipment.art_shipment.get_connected_purchase_receipt', {
				art_shipment: frm.doc.name
			}).then(r => {
				console.log(r,'r')
				if (r.message && r.message != undefined) {
					let count=r.message.length
					let link = $(`
			<div class="document-link" data-doctype="Purchase Receipt">
				<div class="document-link-badge" data-doctype="Purchase Receipt"> <span class="count">${count}</span> <a
					class="badge-link">Purchase Receipt</a> </div> <span class="open-notification hidden"
				title="Open Purchase Receipt"> </span></div>
			`);

					link.on('click', function () {
						frappe.route_options = {
							'name': ['in', r.message]
						};
						frappe.set_route("List", "Purchase Receipt", "List");

					})
					$('div').find('.document-link[data-doctype="Supplier Packing List Art"]').before(link);
				}
			})
		}	
	
	}
});