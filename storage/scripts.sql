delete from scouting_reports;
delete from report_requests;
--
-- alter table report_requests
--     drop column if exists user_prompt;
-- alter table report_requests
--     drop column if exists status;
-- alter table report_requests
--     add status varchar(50) default 'pending'::character varying;
-- alter table report_requests
--     add user_prompt text default ''::text not null;

-- alter table report_requests
--     drop column if exists team_id;
-- alter table report_requests
--     drop column if exists time_window;
-- alter table report_requests
--     drop column if exists team_fk_id;
-- alter table report_requests
--     drop column if exists team_name