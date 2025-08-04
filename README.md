haha


```
commit 7f4c2a10d5c3c837a5e44f87b6a889a9e12eab7c
Author: Alice Lee <alice@example.com>
Date:   Tue Jul 23 16:45:12 2024 +0900

    Fix: handle empty list in process_data

diff --git a/src/utils/data.py b/src/utils/data.py
--- a/src/utils/data.py
+++ b/src/utils/data.py
@@ def process_data(dataset):
-    if not dataset:
-        return []
+    if dataset is None or len(dataset) == 0:
+        return []

     return [d.strip() for d in dataset]

commit 4a2b991be78a84c5d7b94d82a9a1cd5076b65c2f
Author: Bob Kim <bob@example.com>
Date:   Mon Jul 15 10:01:03 2024 +0900

    Refactor: simplify process_data logic

```
