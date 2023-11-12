import json
import ai_read_file as rf

dataset_name = input("Dataset name: ")
subsets = {}
i = 1
s = 1

while True:
    try:
        subset_name = input("Subset #" + str(i) + " name (leave blank when done): ")

        if (len(subset_name.strip()) <= 0):
            break

        while True:
            subset_split = input("Subset #" + str(i) + " split #" + str(s) + " name (leave blank when done): ")

            if (len(subset_split.strip()) <= 0):
                break

            subset_path = input("Subset #" + str(i) + " split #" + str(s) + " file path: ")

            subsets[subset_name] = {}
            subsets[subset_name][subset_split] = {"text": rf.read_lines_from_file(subset_path)}

            s += 1
        
        i += 1
        print("Added/Replaced subset '" + subset_name + "' without errors!")
    except Exception as ex:
        print("Error adding subset: " + str(ex))

with open(dataset_name + ".json", "w+") as f:
    f.write(json.dumps(subsets))
    f.close()

full_subsets = ""

for i in list(subsets.values()):
    for g in list(i.values()):
        full_subsets += "".join(l for l in g["text"])

dataset_info = {
    "vocab_size": len(sorted(list(set(full_subsets)))),
    "length": len(full_subsets),
    "name": dataset_name
}

print("Dataset created successfully!")
print("Dataset information: " + str(dataset_info))