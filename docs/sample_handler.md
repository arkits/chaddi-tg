# Sample Handler

```python
from loguru import logger
from util import util
import traceback


def handle(update, context):

    try:

        util.log_chat("default", update)

    except Exception as e:
        logger.error(
            "Caught Error in default.handle - {} \n {}", e, traceback.format_exc(),
        )
```
