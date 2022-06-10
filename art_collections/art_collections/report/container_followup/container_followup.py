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
                case when nullif(pr.pr_name,'') is not null then 1 else 0 end is_container_recieved ,
                spl.spl_name , spl.supplier , po.po_name , if(po.set_apart_art=1,'Yes','No') set_apart_art , 
                spl.container_count , pr.pr_name , pr.pr_address_title
            from 
                `tabArt Shipment` tas 
                left outer join `tabArt Shipment Container` tasc on tasc.parent = tas.name
                left outer join (
                    select det.container , count(det.container) container_count, CONCAT_WS(', ', p.supplier) supplier , 
                    CONCAT_WS(', ', det.parent) spl_name
                    from `tabSupplier Packing List Detail Art` det
                    inner join `tabSupplier Packing List Art` p on p.name = det.parent 
                    group by container
                ) spl on spl.container = tasc.container_name 
                left outer join (
                    select container_number_art , CONCAT_WS(', ', name) po_name ,
                    max(set_apart_art) set_apart_art
                    from `tabPurchase Order` tpoi 
                    group by container_number_art 
                ) po on po.container_number_art =tasc.container_name
                left outer join (
                    select tpo.container_number_art , CONCAT_WS(', ', tpri.parent) pr_name ,
                    CONCAT_WS(', ', ta.address_title) pr_address_title 
                    from `tabPurchase Receipt Item` tpri 
                    inner join `tabPurchase Receipt` tpr on tpr.name = tpri.parent 
                    left outer join tabAddress ta on ta.name = tpr.shipping_address 
                    inner join `tabPurchase Order` tpo on tpo.name = tpri.purchase_order 
                    group by tpo.container_number_art
                ) pr on pr.container_number_art = tasc.container_name 
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
        Received is for Container,is_container_recieved,Check,130
        SPL #,spl_name,,,130
        PO,po_name,,,130
        Outer Qty,total_outer_qty,Int,,130
        Total Qty,container_count,Int,,130
        Transport Type,type_of_reception,,,130
        Transport Size,size,,,130
        Shipping Date,shipping_date,Date,,130
        Arrival Forecast Date,arrival_forecast_date,Date,,130
        Arrival Forecast Hour,arrival_forecast_hour,,,130
        Purchase Receipt,pr_name,,,180
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
