frappe.ui.form.on('Delivery Note', {
    before_submit: function (frm) {
     if (frm.doc.double_check_order_flag_art==1 && frm.doc.did_you_double_check_the_order_art!=1) 
     {
		frappe.throw(__('You have not double checked the order.'));
     }
    }
 });