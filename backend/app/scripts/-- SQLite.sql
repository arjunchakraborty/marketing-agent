```sql
SELECT 
    business_name,
    category,
    total_conversion / total_sessions AS total_conversion_rate
FROM 
    "avalon_sunshine_acquisition_sessions_by_referrer_add_filter_and_add_bounce_rate_added_to_cart_reached_checkout_conversion_rate_and_sessions_converted_avalon_sunshine_acquisition"
WHERE 
    business_name = 'Avalon_Sunshine'
LIMIT 50;
```