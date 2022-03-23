
$(document).ready(function () {

    frappe.realtime.on("show_email_dialog", function (args) {
        if (cur_frm) {
            let frm = cur_frm;
            if (args && args.doctype == frm.doctype && args.docname == frm.docname) {
                cur_frm.reload_doc().then(() => {
                    frappe.show_email_dialog(frm);
                });
            }
        }
    });
});



frappe.show_email_dialog = function (frm) {
    // show email dialog with pre-set values for default print format 
    // and email template and attach_print

    let composer = new frappe.views.CommunicationComposer({
        doc: frm.doc,
        frm: frm,
        subject: __(frm.meta.name) + ': ' + frm.docname,
        recipients: frm.doc.email || frm.doc.email_id || frm.doc.contact_email,
        attach_document_print: true,
        real_name: frm.doc.real_name || frm.doc.contact_display || frm.doc.contact_name
    });


    frappe.db.get_single_value('Art Collections Settings', 'sales_order_email_template')
        .then(email_template => {
            setTimeout(() => {
                composer.dialog.fields_dict['select_attachments'].$wrapper.find("input").attr("checked", "checked");
                composer.dialog.fields_dict['content'].set_value("");
                composer.dialog.set_values({
                    "email_template": email_template,
                    // "select_print_format": 'Art Collections Sales Order'
                });
            }, 900);
        });
}
