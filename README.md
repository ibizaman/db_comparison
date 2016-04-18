Test performances of various databases
======================================

And save the monitored values in a PostgreSQL database.

Example usage:
```bash
git clone https://github.com/ibizaman/db_comparison
pip3 -r db_comparison/requirements.txt
python3 db_comparison init
python3 db_comparison --help
python3 db_comparison postgres --help
sudo python3 db_comparison postgres create_table
sudo python3 db_comparison postgres insert_batch --num_rows 1000000
```
You will need to use sudo for most of the tests because some of the
monitored parameters require root privileges to be taken.

For now, only PostgreSQL is supported.


Show values in an html page
---------------------------

```
python3 db_comparison server --port 9999
```

Now, in your browser, go to [http://localhost:9999](http://localhost:9999)
to see the two results above.

![Screenshot of example plot](https://cloud.githubusercontent.com/assets/1044950/14593441/544340de-04df-11e6-8e0e-050cc772cdcf.png)

