with 

agreements as (

    select * from {{ ref('dim_agreements') }}

),

fiscal_years as (

    select * from {{ ref('stg_postgres__fiscal_years') }}

),

int_combined_revenue as (

    select * from {{ ref('int_combined_net_revenue') }}

),

expiring_agreements as (

    select
        icr.agreement_id,
        icr.account_id,
        icr.property_id,
        icr.org_id,
        max(fy.label) as expiring_fiscal_year

    from int_combined_revenue icr
    inner join fiscal_years fy on fy.id = icr.fiscal_year_id
    inner join agreements a on a.id = icr.agreement_id
    where a.salesforce_id is null
    group by 1,2,3,4

),

expiring_agreements_salesforce_by_property_and_account as ( -- includes van wagner

    select
        icr.account_id,
        icr.property_id,
        icr.org_id,
        max(fy.label) as expiring_fiscal_year

    from int_combined_revenue icr
    inner join fiscal_years fy on fy.id = icr.fiscal_year_id
    inner join agreements a on a.id = icr.agreement_id
    where a.percent_closed_value = 1 and a.salesforce_id is not null
    group by 1,2,3
    order by icr.account_id

),

expiring_agreements_salesforce as ( -- includes van wagner

    select
        icr.agreement_id,
        icr.account_id,
        icr.property_id,
        icr.org_id,
        easbpaa.expiring_fiscal_year as expiring_fiscal_year

    from int_combined_revenue icr
    inner join fiscal_years fy on fy.id = icr.fiscal_year_id
    inner join expiring_agreements_salesforce_by_property_and_account easbpaa on icr.property_id = easbpaa.property_id and icr.account_id = easbpaa.account_id and icr.org_id = easbpaa.org_id and fy.label = easbpaa.expiring_fiscal_year
    order by icr.agreement_id

),

final as (

    select
        ea.agreement_id,
        ea.account_id,
        ea.property_id,
        ea.org_id,
        ea.one

    from expiring_agreements ea
    union all
    select
        eavw.agreement_id,
        eavw.account_id,
        eavw.property_id,
        eavw.org_id,
        eavw.one

    from expiring_agreements_salesforce eavw

)

select * from final