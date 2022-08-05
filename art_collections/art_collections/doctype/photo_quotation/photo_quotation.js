// Copyright (c) 2022, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Photo Quotation', {
	refresh: function (frm) {
		make_items_grid(frm);

		frm.trigger("add_custom_buttons");
	},

	add_custom_buttons: function (frm) {
		frm.add_custom_button(__("Bulk Photo Import"), function () {
			new frappe.ui.FileUploader({
				method: "art_collections.art_collections.doctype.photo_quotation.photo_quotation.import_lead_item_photos",
				doctype: frm.doctype,
				docname: frm.docname,
				frm: frm,
				folder: 'Home/Attachments',
				on_success: (file_doc) => {
					// console.log(file_doc);
				}
			})
		}, __("Tools"));

		frm.add_custom_button(__("Create Items"), function () {
			frappe.confirm("10 Items will be created. Do you wish to proceed?", () => { });
		}, __("Tools"));

		frm.add_custom_button(__("Email Supplier for Quotation"), function () {
			return frm.call({
				method: 'get_supplier_email',
				doc: frm.doc,
				args: {
					template: "supplier_quotation"
				}
			});
		}, __("Tools"));


		frm.add_custom_button(__("Email Supplier for Sample"), function () {
			return frm.call({
				method: 'get_supplier_email',
				doc: frm.doc,
				args: {
					template: "supplier_sample_request"
				}
			});
		}, __("Tools"));

	},

	before_save: function (frm) {
		let data = window.items_table.getData();
		return frm.call({
			method: 'update_lead_items',
			doc: frm.doc,
			args: {
				items: data
			}
		});
	},

	upload_items: function (frm) {
		new frappe.ui.FileUploader({
			as_dataurl: true,
			allow_multiple: false,
			on_success(file) {
				var reader = new FileReader();
				reader.onload = function (e) {
					var workbook = XLSX.read(e.target.result);
					var csv = XLSX.utils.sheet_to_csv(workbook.Sheets['Lead Items']);
					var data = frappe.utils.csv_to_array(csv);
					window.items_table.setData(data.slice(1));
					frm.dirty();
				}
				reader.readAsArrayBuffer(file.file_obj)
			}
		})
	},

	make_items_grid: function (frm) {
		make_items_grid(frm);
	},

	download_items: function (template) {
		// let data = [window.items_table.getHeaders().split(",")].concat(window.items_table.getData());
		// const worksheet = XLSX.utils.aoa_to_sheet(data);
		// const workbook = XLSX.utils.book_new();
		// XLSX.utils.book_append_sheet(workbook, worksheet, 'Lead Items');
		// XLSX.writeFile(workbook, cur_frm.doc.name + "-Lead Items.xlsx");
		open_url_post(
			'/api/method/art_collections.art_collections.doctype.photo_quotation.photo_quotation.download_lead_items_template'
			, {
				docname: cur_frm.doc.name,
				template: template
			});
	}
});



function make_items_grid(frm) {
	if (window.items_table)
		jspreadsheet.destroy(document.getElementById('items-table'), false);
	// 
	const tmpl = `<div id="items-table"></div>`;
	let items_html = frm.fields_dict["items_html"];
	items_html.$wrapper.html(tmpl)
	let width = items_html.$wrapper.closest('div.section-body').width()

	frm.call({
		method: 'get_lead_items',
		doc: frm.doc,
		args: {}
	}).then((r) => {

		let columns = r.message.columns.map(t => {
			return {
				title: t.label,
				type: t.fieldtype
			}
		})

		// https://bossanova.uk/jspreadsheet/v4/docs/quick-reference
		let items_table = jspreadsheet(document.getElementById('items-table'), {
			filters: true,
			columns: columns,
			minDimensions: [columns.length, 3],
			defaultColWidth: 100,
			tableOverflow: true,
			tableWidth: `${width - 30}px`,
			tableHeight: "500px",
			search: true,
			freezeColumns: 2,
			// pagination: 10,
			updateTable: function (instance, cell, col, row, val, id) {
				if (col == 1 && val) {
					cell.innerHTML = '<img src="' + val + '" style="width:40px;height:40px">';
				}
			},
			onafterchanges: function (instance) {
				frm.dirty();
			}
		});
		items_table.setData(r.message.data)
		setup_toolbar();
		window.items_table = items_table;

	});

	function setup_toolbar() {
		let html = `
		<div>
			<div id="templates"></div>
			<button onclick="cur_frm.events.upload_items(cur_frm)">Upload</button>
			<button onclick="cur_frm.trigger('make_items_grid')">Reload Items</button>
		</div>
		`
		$(html).appendTo('.jexcel_filter')
		jSuites.dropdown(document.getElementById('templates'), {
			data: [
				{ text: 'Artyfetes', value: 'artyfetes' },
				{ text: 'Supplier', value: 'supplier_quotation' },
				{ text: 'Sample Request', value: 'supplier_sample_request' },
				{ text: 'Create Items', value: 'create_items' },
				{ text: 'All Columns', value: 'all' },
			],
			placeholder: "Select Template to Dowmload",
			width: '240px',
			onchange: function (el, value) {
				cur_frm.events.download_items(el.value);
			},
		});

		$('.jexcel_filter').css('justify-content', 'right')

	}

}
