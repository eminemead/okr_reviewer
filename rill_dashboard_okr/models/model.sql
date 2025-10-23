-- Model SQL
-- Reference documentation: https://docs.rilldata.com/reference/project-files/models

-- Joined model of okr_metric and dim_fellow
-- NOTE: Adjust the join key(s) below if your schema differs.
-- Common options: employee_id, email, user_id

select
  m.*,
  f.*
from okr_metric as m
left join dim_fellow as f
  on m.owner = f.fellow_ad_account