# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    return get_columns(filters), get_data(filters)


def get_data(filters=None):

    data = frappe.db.sql(
        """
select 
                tas.name , tas.owner ,
                tasc.container_name , tasc.type_of_reception , tas.shipping_date ,
                tasc.arrival_forecast_date , tasc.arrival_forecast_hour , tas.telex_release_sent_date ,
                tasc.total_outer_qty , 
                case when nullif(spl.pr_name,'') is not null then 'Yes' else 'No' end is_container_recieved ,
                spl.spl_name , spl.supplier , spl.po_name , if(spl.set_apart_art=1,1,0) set_apart_art , 
                spl.container_count , spl.pr_name , spl.pr_address_title ,
                case when tasc.type_of_reception = 'FCL' then tasc.container_size
                	else tasc.qty_of_pallet end transport_size
            from 
                `tabArt Shipment` tas 
                left outer join `tabArt Shipment Container` tasc on tasc.parent = tas.name
                left outer join (
                    select det.container , count(det.container) container_count, 
                    GROUP_CONCAT(DISTINCT concat(p.supplier,':',tsup.supplier_name) ORDER BY p.supplier) supplier , 
                    GROUP_CONCAT(DISTINCT det.parent ORDER BY det.creation) spl_name , 
                    GROUP_CONCAT(DISTINCT det.purchase_order ORDER BY tpo2.transaction_date ) po_name ,
                    max(set_apart_art) set_apart_art ,
                    GROUP_CONCAT(DISTINCT tpri.parent ORDER BY tpr.posting_date) pr_name , 
                    GROUP_CONCAT(DISTINCT ta.address_title) pr_address_title 
                    from `tabSupplier Packing List Detail Art` det
                    inner join `tabSupplier Packing List Art` p on p.name = det.parent 
                    left outer join tabSupplier tsup on tsup.name = p.supplier
                    left outer join `tabPurchase Order` tpo2 on tpo2.name = det.purchase_order
                    left outer join `tabPurchase Receipt Item` tpri on tpri.purchase_order = tpo2.name
                    left outer join `tabPurchase Receipt` tpr on tpr.name = tpri.parent 
                    left outer join tabAddress ta on ta.name = tpr.shipping_address                     
                    group by container
                ) spl on spl.container = tasc.container_name 
                """.format(
            conditions=get_conditions(filters)
        ),
        filters,
        as_dict=True,
        # debug=True,
    )

    return data


def get_columns(filters):
    return csv_to_columns(
        """
        Shipment Name,name,Link,Art Shipment,140
        Created By,owner,Link,User,120
        Container #,container_name,,,145
        Received is for Container,is_container_recieved,,130
        SPL #,spl_name,,,200
        Supplier,supplier,,,200
        PO,po_name,,,200
        Outer Qty,total_outer_qty,Int,,130
        Total Qty,container_count,Int,,130
        Transport Type,type_of_reception,,,130
        Transport Size,transport_size,,,130
        Shipping Date,shipping_date,Date,,130
        Set Apart,set_apart_art,Int,,130
        Arrival Forecast Date,arrival_forecast_date,Date,,130
        Arrival Forecast Hour,arrival_forecast_hour,,,130
        Purchase Receipt,pr_name,,,200
        Purchase Receipt Address,pr_address_title,,,300
        Telex Release Sent Date,telex_release_sent_date,Date,,130
        """
    )


def get_conditions(filters):
    conditions = []
    return conditions and " and " + " and ".join(conditions) or ""


def csv_to_columns(csv_str):
    props = ["label", "fieldname", "fieldtype", "options", "width"]
    return [
        zip(props, [x.strip() for x in col.split(",")])
        for col in csv_str.split("\n")
        if col.strip()
    ]
