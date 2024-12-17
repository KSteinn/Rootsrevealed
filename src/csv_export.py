from python_gedcom_2.parser import Parser
from python_gedcom_2.element.individual import IndividualElement
import typing
import csv

file_path = "The English and British Kings and Queens.ged"
p: Parser = Parser()
p.parse_file(file_path)

invid = []
for element in p.get_root_child_elements():
    if isinstance(element,IndividualElement):
        invid.append(element)

data = []
#, i.get_death_element()
for i in invid:
    if i.get_birth_element():
        if i.get_birth_element().has_date():
            birt = str(i.get_birth_element().get_date_element().as_datetime())[:-9]
        else:
            birt = None
    else:
        birt = None

    if i.get_death_element():
        if i.get_death_element().has_date():
            deat = str(i.get_death_element().get_date_element().as_datetime())[:-9]
        else:
            deat = None
    else:
        deat = None

    children = p.get_children(i)
    child_names = ""
    for child in children:
        child_names += child.get_name() +"; "
    child_names = child_names[:-2] 

    parents = p.get_parents(i)
    parent_str = ""
    for parent in parents:
        if parent:
            parent_str += parent.get_name() + "; "
    parent_str = parent_str[:-2] 


    data.append([i.get_name(), i.get_gender(), i.get_occupation(), birt, deat, child_names, parent_str])
    #data.append(i.get_events())

print(data)

data_dicts = [dict(zip(["Name", "Gender", "Arbeit", "Geburt", "Tod", "Kinder", "Eltern (V,M)"], row)) for row in data]


with open('ances.csv', 'w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.DictWriter(
        csvfile,
        fieldnames=["Name", "Gender", "Arbeit", "Geburt", "Tod", "Kinder", "Eltern (V,M)"],
        delimiter=',',
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL
    )
    # Write header row
    csvwriter.writeheader()
    
    # Write data rows
    csvwriter.writerows(data_dicts)

