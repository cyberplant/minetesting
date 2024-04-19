import re
import sys
from collections import defaultdict

if len(sys.argv) < 2:
    print("Usage: {sys.argv[0]} [networkprotocol.h file location]")
    sys.exit(1)

filename=sys.argv[1]
data = defaultdict(dict)
comment_mode = False
s = True

print(f"Reading {filename} ..")
with open(filename) as f:
    while s:
        s = f.readline()
        if comment_mode:
            if "*/" in s:
                comment_mode = False
            else:
                continue

        if "/*" in s:
            comment_mode = True

        m = re.match("[\s]*(\S*).* = (.*)[,]", s)
        if not m:
            continue

        var_name = m.group(1)
        var_value = m.group(2)
        var_group = var_name[:var_name.index("_")]
        var_id = var_name[var_name.index("_")+1:]

        data[var_group][var_id] = var_value

print(f"Writing networkprotocol.py..")

f = open("networkprotocol.py", "w")
for vargroup_name in data:
    f.write(f"{vargroup_name} = {{\n")
    for variable in data[vargroup_name]:
        value = data[vargroup_name][variable]
        f.write(f'   "{variable}": {value},\n')
    f.write("}\n\n")

print(f"Done.")
