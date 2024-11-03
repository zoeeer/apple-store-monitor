# Apple Store Monitor

Because the iPhone 16 series sell out very quickly, I wrote this program to monitor the availability of the products.

## What it does

1. Check the availability of the products by making request to the Apple Store website.
2. Save the availability history in the database, grouped by store and product model.
3. Run the procedure with a [schedule](https://schedule.readthedocs.io/en/stable/).
4. Send notification \[[PushDeer](https://github.com/easychen/pushdeer)\] when the availability changes.
