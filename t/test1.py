import json
from dataroute import DataRoute


def main():
    correct_input = """
sourse=dict

target1=dict("target_new")

target1:
    [name] -> |*lower| -> [](int)
"""

    dtrt = DataRoute(correct_input, debug=False, lang="", color=True)
    result = dtrt.go()
    dtrt.print_json()


if __name__ == "__main__":
    main() 


{
  "target_new": {
    "sourse_type": "dict",
    "target_type": "dict",
    "routes": {
      "name": {
        "pipeline": {
          "1": {
            "type": "py_func",
            "param": "$this",
            "full_str": "*lower"
          }
        },
        "final_type": "__void__",
        "final_name": "__void__"
      }
    }
  }
}