from typing import List, Dict, Any
from copy import deepcopy

class PydictSourceGetter:
    def __init__(self, data: List[Dict[str, Any]], required_keys: List[str]):
        self.data = deepcopy(data)
        self.required_keys = set(required_keys)
        self.report = self._run_validation()

    def _run_validation(self) -> Dict[str, Any]:
        total = len(self.data)
        valid = 0
        invalid = 0
        invalid_examples = []

        for idx, item in enumerate(self.data):
            item_keys = set(item.keys())
            missing_keys = list(self.required_keys - item_keys)

            if not missing_keys:
                valid += 1
            else:
                invalid += 1
                if len(invalid_examples) < 10:
                    invalid_examples.append({
                        "index": idx,
                        "missing_keys": missing_keys
                    })

        percent_valid = round((valid / total * 100), 3) if total > 0 else 0.0

        return {
            "source": "pydict",
            "fully_valid": valid == total,
            "total_received": total,
            "valid_count": valid,
            "invalid_count": invalid,
            "percent_valid": percent_valid,
            "invalid_examples": invalid_examples
        }


# data = [
#     {"name": "Bob"},
#     {"name": "Jack", "age": 53, "extra": "oops"},
#     {"name": "Frank", "age": 28},
#     {"name": "Alice"},
#     {"age": 30},
#     {"name": "Grace", "age": 34},
#     {"name": "Carol", "age": 41},
#     {"name": "Grace", "age": 45, "extra": "debug"},
#     {"name": "Eva", "age": 25},
#     {"name": "Frank"},
#     {"name": "Frank", "age": 33},
#     {"name": "Alice", "age": 44, "extra": "oops"},
#     {"age": 58},
#     {"name": "Bob", "age": 21},
#     {"name": "Hank"},
#     {"name": "Ivy", "age": 50, "extra": "test"},
#     {"name": "Eva", "age": 23},
#     {"name": "David", "age": 49},
#     {"name": "Hank"},
#     {"name": "Frank", "age": 60, "extra": "extra1"},
#     {"name": "Jack"},
#     {"name": "Grace", "age": 38},
#     {"age": 24},
#     {"name": "Alice", "age": 63, "extra": "debug"},
#     {"name": "Ivy", "age": 29},
#     {"name": "Bob"},
#     {"name": "Carol", "age": 45},
#     {"name": "Grace", "age": 31},
#     {"name": "Eva", "age": 22, "extra": "oops"},
#     {"name": "Frank"},
#     {"name": "Alice", "age": 35},
#     {"name": "Carol"},
#     {"age": 39},
#     {"name": "Hank", "age": 59},
#     {"name": "Ivy", "age": 42, "extra": "test"},
#     {"name": "David", "age": 20},
#     {"name": "Grace"},
#     {"name": "Jack", "age": 61},
#     {"name": "Bob", "age": 47, "extra": "extra1"},
#     {"name": "Carol", "age": 27},
#     {"name": "David"},
#     {"name": "Alice", "age": 26},
#     {"name": "Eva"},
#     {"age": 37},
#     {"name": "Ivy", "age": 36},
#     {"name": "Hank", "age": 31},
#     {"name": "Frank", "age": 22, "extra": "debug"},
#     {"name": "Bob"},
#     {"name": "Carol", "age": 30}
# ]


# getter = PydictSourceGetter(data, required_keys=["name", "age"])

# from pprint import pprint
# pprint(getter.report)
