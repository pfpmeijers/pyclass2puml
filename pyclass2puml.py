from typing import List
from os import listdir
import re


def parse_class_names(lines_in) -> List[str]:
    class_names = []
    for in_line in lines_in:
        match = re.match("class\s+(\w+)", in_line)
        if match:
            groups = match.groups()
            class_names.append(groups[0])
    return class_names


def parse_class_line(in_line: str, domain: str) -> (str, str, str):
    # Prefix class names with domain name
    # Replace class inheritance by explicit relation
    out_line = in_line
    relation = None
    class_name = None
    match = re.match("\s*class\s+(\w+)(\((\w|\.)+\))?\s*:", in_line)
    if match:
        groups = match.groups()
        class_name = groups[0]
        class_base = groups[1][1:-1] if groups[1] else None
        if class_base:
            if class_base.startswith("\""):
                class_base = class_base[1:-1]
            out_line = f"class {domain}.{class_name} {{\n"
            if class_base.find(".") == -1:
                class_base = f"{domain}.{class_base}"
            relation = f"{class_base} <|-- {domain}.{class_name}\n"
        else:
            out_line = f"class {domain}.{class_name} {{\n"
    return out_line, relation, class_name

def parse_attribute_line(in_line: str, domain: str, current_class_name: str, class_names: List[str]) -> (str, str, str):
    # Add relations for each type references
    out_line = in_line
    relation = None
    attr_name = None
    match = re.match("\s*(\w+)\s*:\s*(\S+)", in_line)
    if match:
        groups = match.groups()
        attr_name = groups[0]
        type_name = groups[1]
        multi = False
        if type_name.startswith("List"):
            multi = True
            type_name = type_name[5:-1]
        if type_name.startswith("\""):
            type_name = type_name[1:-1]
        external_type = type_name.find(".") != -1
        if external_type or type_name in class_names:
            referred_class_name = type_name if external_type else f"{domain}.{type_name}"
            relation = f"{domain}.{current_class_name} ---> \"{'*' if multi else '1'}\" {referred_class_name}\n"
        out_line = f"    {attr_name}: {f'List[{type_name}]' if multi else type_name}\n"
    return out_line, relation, attr_name


def process(dir_name, out_name):
    out_file = open(out_name, "w")
    out_file.writelines("@startuml\n")

    relations = []
    for file_name in listdir(dir_name):
        if file_name.endswith(".py"):
            domain = file_name.split(".")[0]
            py_file = open(f"{dir_name}/{file_name}", "r")
        else:
            continue

        lines = []
        for line in py_file:
            lines.append(line)

        class_names = parse_class_names(lines)

        current_class_name = ""
        for line in lines:

            line, relation, class_name = parse_class_line(line, domain)
            if class_name:
                if current_class_name:
                    line = "}\n" + line
                out_file.writelines([line])
                current_class_name = class_name
                if relation:
                    relations.append(relation)
                continue

            line, relation, attr_name = parse_attribute_line(line, domain, current_class_name, class_names)
            if attr_name:
                out_file.writelines([line])
                if relation:
                    relations.append(relation)

        if current_class_name:
            line = "}\n"
            out_file.writelines([line])

    out_file.writelines(relations)
    out_file.writelines("@enduml\n")
    out_file.close()


if __name__ == "__main__":

    from sys import argv

    if len(argv) < 2 or len(argv) > 3:
        print("usage: pyclass2puml py-directory [output-file]")
        exit()

    dir_name = argv[1]
    out_name = f"{dir_name}.puml" if len(argv) == 2 else argv[2]

    process(dir_name, out_name)