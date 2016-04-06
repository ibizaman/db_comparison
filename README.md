Test performances of various databases
======================================

And save the monitored values in a PostgreSQL database.

```
git clone https://github.com/ibizaman/db_comparison
pip3 -r db_comparison/requirements.txt
python3 db_comparison/setup_result_db.py
python3 db_comparison --help
python3 db_comparison postgres create_table
```

For now, only PostgreSQL is supported.
