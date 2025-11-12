import duckdb

conn = duckdb.connect("/Users/xiaofei.yin/rill_test.db")
try:
    rows = conn.execute("""
        SELECT COUNT(*) FROM onvo_employee_fellow_maturity_info_1d_a
        WHERE
            fellow_emp_status_name = '在职'
            AND is_intern = FALSE
            AND fellow_ad_account IS NOT NULL
            AND fellow_workday_cn_title IN ('乐道区域总经理', '乐道区域副总经理', '乐道销售部负责人', '乐道片区总', '乐道行销大区负责人', '乐道区域行销负责人', '乐道战队长', '乐道行销战队长')
    """).fetchall()
    print(f"Number of manager users to process: {rows[0][0]}")
finally:
    conn.close()
