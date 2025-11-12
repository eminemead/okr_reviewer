import duckdb

def main():
    db_path = "/Users/xiaofei.yin/rill_test.db"
    conn = duckdb.connect(db_path)
    try:
        result = conn.execute("""
            SELECT fellow_workday_cn_title, COUNT(*) as count
            FROM onvo_employee_fellow_maturity_info_1d_a
            WHERE 
                fellow_emp_status_name = '在职'
                AND is_intern = FALSE
                AND fellow_ad_account IS NOT NULL
                AND fellow_workday_cn_title IN ('乐道区域总经理', '乐道区域副总经理', '乐道销售部负责人', '乐道片区总', '乐道行销大区负责人', '乐道区域行销负责人', '乐道战队长', '乐道行销战队长')
            GROUP BY fellow_workday_cn_title
            ORDER BY count DESC
        """).fetchall()
        print("Title counts:")
        for title, count in result:
            print(f"{title}: {count}")
        total = sum(count for _, count in result)
        print(f"Total: {total}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
