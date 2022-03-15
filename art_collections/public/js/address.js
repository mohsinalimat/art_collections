frappe.ui.form.on('Address', {

    delivery_contact_art: function (frm) {
        
        if (frm.doc.delivery_contact_art) {
            frappe.db.get_value('Contact', frm.doc.delivery_contact_art, ['first_name', 'last_name','email_id','mobile_no'])
            .then(r => {
                let values = r.message;
                frm.doc.delivery_appointment_contact_detail_art=__('First Name :')+(values.first_name || '')+'\n'+__('Surname :')+(values.last_name || '')+'\n'
                +__('Mobile :')+(values.mobile_no || '')+'\n'+__('Email :')+(values.email_id || '')
                frm.refresh_field('delivery_appointment_contact_detail_art')
            })            
        }
       

    },
   validate: function (frm) {
    if (frm.doc.art_county) 
    {
        frm.doc.county=frm.doc.art_county
    }
    if (frm.doc.art_state) 
    {
        frm.doc.state=frm.doc.art_state
    }
   }
});