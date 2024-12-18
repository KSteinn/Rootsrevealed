"""
Module containing the actual `gedcom.parser.Parser` used to generate elements - out of each line -
which can in return be manipulated.
"""

import re as regex
from sys import version_info, stdout
from typing import List, Tuple

from python_gedcom_2.element_creator import ElementCreator
from python_gedcom_2.element.element import Element
from python_gedcom_2.element.family import FamilyElement
from python_gedcom_2.element.individual import IndividualElement, NotAnActualIndividualError
from python_gedcom_2.element.root import RootElement
import python_gedcom_2.tags

FAMILY_MEMBERS_TYPE_ALL = "ALL"
FAMILY_MEMBERS_TYPE_CHILDREN = python_gedcom_2.tags.GEDCOM_TAG_CHILD
FAMILY_MEMBERS_TYPE_HUSBAND = python_gedcom_2.tags.GEDCOM_TAG_HUSBAND
FAMILY_MEMBERS_TYPE_PARENTS = "PARENTS"
FAMILY_MEMBERS_TYPE_WIFE = python_gedcom_2.tags.GEDCOM_TAG_WIFE


class GedcomFormatViolationError(Exception):
    pass


class PointerNotFoundException(Exception):
    pass


class Parser:
    """Parses and manipulates GEDCOM 5.5 format data

    For documentation of the GEDCOM 5.5 format, see: https://homepages.rootsweb.com/~pmcbride/gedcom/55gctoc.htm

    This parser reads and parses a GEDCOM file.

    Elements may be accessed via:

    * a `list` through `gedcom.parser.Parser.get_element_list()`
    * a `dict` through `gedcom.parser.Parser.get_element_dictionary()`
    """

    def __init__(self):
        self.__element_list = []
        self.__element_dictionary = {}
        self.__root_element = RootElement()

    def invalidate_cache(self):
        """Empties the element list and dictionary to cause `gedcom.parser.Parser.get_element_list()`
        and `gedcom.parser.Parser.get_element_dictionary()` to return updated data.

        The update gets deferred until each of the methods actually gets called.
        """
        self.__element_list = []
        self.__element_dictionary = {}

    def get_element_by_pointer(self, pointer: str) -> Element | None:
        """Returns the element that has the provided pointer. Returns None if no Element with that pointer doesn't exist.
        """
        element_dictionary = self.get_element_dictionary()
        if pointer not in element_dictionary:
            return None
        else:
            return element_dictionary[pointer]

    def get_element_list(self) -> List[Element]:
        """Returns a list containing all elements from within the GEDCOM file

        By default elements are in the same order as they appeared in the file.

        This list gets generated on-the-fly, but gets cached. If the database
        was modified, you should call `gedcom.parser.Parser.invalidate_cache()` once to let this
        method return updated data.

        Consider using `gedcom.parser.Parser.get_root_element()` or `gedcom.parser.Parser.get_root_child_elements()` to access
        the hierarchical GEDCOM tree, unless you rarely modify the database.
        """
        if not self.__element_list:
            for element in self.get_root_child_elements():
                self.__build_list(element, self.__element_list)
        return self.__element_list

    def get_element_dictionary(self) -> dict[str, Element]:
        """Returns a dictionary containing all elements, identified by a pointer, from within the GEDCOM file

        Only elements identified by a pointer are listed in the dictionary.
        The keys for the dictionary are the pointers.

        This dictionary gets generated on-the-fly, but gets cached. If the
        database was modified, you should call `invalidate_cache()` once to let
        this method return updated data.
        """
        if not self.__element_dictionary:
            self.__element_dictionary = {
                element.get_pointer(): element for element in self.get_root_child_elements() if element.get_pointer()
            }

        return self.__element_dictionary

    def get_root_element(self):
        """Returns a virtual root element containing all logical records as children

        When printed, this element converts to an empty string.

        :rtype: RootElement
        """
        return self.__root_element

    def get_root_child_elements(self):
        """Returns a list of logical records in the GEDCOM file

        By default, elements are in the same order as they appeared in the file.

        :rtype: list of Element
        """
        return self.get_root_element().get_child_elements()

    def parse_file(self, file_path, strict=True):
        """Opens and parses a file, from the given file path, as GEDCOM 5.5 formatted data
        :type file_path: str
        :type strict: bool
        """
        with open(file_path, 'rb') as gedcom_stream:
            self.parse_stream(gedcom_stream, strict)

    def parse_stream(self, gedcom_stream, strict=True):
        """Parses a stream, or an array of lines, as GEDCOM 5.5 formatted data
        :type gedcom_stream: a file stream, or str array of lines with new line at the end
        :type strict: bool
        """
        self.invalidate_cache()
        self.__root_element = RootElement()

        line_number = 1
        last_element = self.get_root_element()

        for line in gedcom_stream:
            last_element = self.parse_line(line_number, line.decode('utf-8-sig'), last_element, strict)
            line_number += 1

    def parse(self, string: str, strict=True):
        """Parses a stream, or an array of lines, as GEDCOM 5.5 formatted data"""
        self.invalidate_cache()
        self.__root_element = RootElement()

        line_number = 1
        last_element = self.get_root_element()

        for line in string.strip().split("\n"):
            last_element = self.parse_line(line_number, line, last_element, strict)
            line_number += 1

    # Private methods

    @staticmethod
    def parse_line(line_number: int, line: str, last_element: Element, strict=True) -> Element:
        """Parse a line from a GEDCOM 5.5 formatted document

        Each line should have the following (bracketed items optional):
        level + ' ' + [pointer + ' ' +] tag + [' ' + line_value]
        """

        # Level must start with non-negative int, no leading zeros.
        level_regex = '^(0|[1-9]+[0-9]*) '

        # Pointer optional, if it exists it must be flanked by `@`
        pointer_regex = '(@[^@]+@ |)'

        # Tag must be an alphanumeric string
        tag_regex = '([A-Za-z0-9_]+)'

        # Value optional, consists of anything after a space to end of line
        value_regex = '( [^\n\r]*|)'

        # End of line defined by `\n` or `\r`
        end_of_line_regex = '([\r\n]{1,2})'

        # Complete regex
        gedcom_line_regex = level_regex + pointer_regex + tag_regex + value_regex + end_of_line_regex
        regex_match = regex.match(gedcom_line_regex, line)

        if regex_match is None:
            if strict:
                error_message = (f"Line <{line_number}:{line}> of document violates GEDCOM format 5.5"
                                 + "\nSee: https://chronoplexsoftware.com/gedcomvalidator/gedcom/gedcom-5.5.pdf")
                raise GedcomFormatViolationError(error_message)
            else:
                # Quirk check - see if this is a line without a CRLF (which could be the last line)
                last_line_regex = level_regex + pointer_regex + tag_regex + value_regex
                regex_match = regex.match(last_line_regex, line)
                if regex_match is not None:
                    line_parts = regex_match.groups()

                    level = int(line_parts[0])
                    pointer = line_parts[1].rstrip(' ')
                    tag = line_parts[2]
                    value = line_parts[3].strip()
                    crlf = '\n'
                else:
                    # Quirk check - Sometimes a gedcom has a text field with a CR.
                    # This creates a line without the standard level and pointer.
                    # If this is detected then turn it into a CONC or CONT.
                    line_regex = '([^\n\r]*|)'
                    cont_line_regex = line_regex + end_of_line_regex
                    regex_match = regex.match(cont_line_regex, line)
                    line_parts = regex_match.groups()
                    level = last_element.get_level()
                    tag = last_element.get_tag()
                    pointer = None
                    value = line_parts[0].strip()
                    crlf = line_parts[1]
                    if tag != python_gedcom_2.tags.GEDCOM_TAG_CONTINUED and tag != python_gedcom_2.tags.GEDCOM_TAG_CONCATENATION:
                        # Increment level and change this line to a CONC
                        level += 1
                        tag = python_gedcom_2.tags.GEDCOM_TAG_CONCATENATION
        else:
            line_parts = regex_match.groups()

            level = int(line_parts[0])
            pointer = line_parts[1].rstrip(' ')
            tag = line_parts[2]
            value = line_parts[3].strip()
            crlf = line_parts[4]

        # Check level: should never be more than one higher than previous line.
        if level > last_element.get_level() + 1:
            error_message = (f"Line {line_number} of document violates GEDCOM format 5.5"
                             + "\nLines must be no more than one level higher than previous line."
                             + "\nSee: https://chronoplexsoftware.com/gedcomvalidator/gedcom/gedcom-5.5.pdf")
            raise GedcomFormatViolationError(error_message)

        element = ElementCreator.create_element(level, pointer, tag, value, crlf, is_multiline=False)

        # Start with last element as parent, back up if necessary.
        parent_element = last_element

        while parent_element.get_level() > level - 1:
            parent_element = parent_element.get_parent_element()

        # Add child to parent & parent to child.
        parent_element.add_child_element(element)

        return element

    def __build_list(self, element, element_list):
        """Recursively add elements to a list containing elements
        :type element: Element
        :type element_list: list of Element
        """
        element_list.append(element)
        for child in element.get_child_elements():
            self.__build_list(child, element_list)

    # Methods for analyzing individuals and relationships between individuals

    def get_marriages(self, individual: IndividualElement) -> List[Tuple[str, str]]:
        """Returns a list of marriages of an individual formatted as a tuple (`str` date, `str` place)
        """
        marriages = []
        if not isinstance(individual, IndividualElement):
            raise NotAnActualIndividualError(
                f"Operation only valid for elements with {python_gedcom_2.tags.GEDCOM_TAG_INDIVIDUAL} tag"
            )
        # Get and analyze families where individual is spouse.
        families = self.get_families(individual, python_gedcom_2.tags.GEDCOM_TAG_FAMILY_SPOUSE)
        for family in families:
            for family_data in family.get_child_elements():
                if family_data.get_tag() == python_gedcom_2.tags.GEDCOM_TAG_MARRIAGE:
                    date = ''
                    place = ''
                    for marriage_data in family_data.get_child_elements():
                        if marriage_data.get_tag() == python_gedcom_2.tags.GEDCOM_TAG_DATE:
                            date = marriage_data.get_value()
                        if marriage_data.get_tag() == python_gedcom_2.tags.GEDCOM_TAG_PLACE:
                            place = marriage_data.get_value()
                    marriages.append((date, place))
        return marriages

    def get_families(self, individual: IndividualElement, family_type=python_gedcom_2.tags.GEDCOM_TAG_FAMILY_SPOUSE) -> List[FamilyElement]:
        """Return family elements listed for an individual

        family_type can be `gedcom.tags.GEDCOM_TAG_FAMILY_SPOUSE` (families where the individual is a spouse) or
        `gedcom.tags.GEDCOM_TAG_FAMILY_CHILD` (families where the individual is a child). If a value is not
        provided, `gedcom.tags.GEDCOM_TAG_FAMILY_SPOUSE` is default value.
        """
        if not isinstance(individual, IndividualElement):
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag" % python_gedcom_2.tags.GEDCOM_TAG_INDIVIDUAL
            )

        families = []
        element_dictionary = self.get_element_dictionary()

        for child_element in individual.get_child_elements():
            is_family = (child_element.get_tag() == family_type
                         and child_element.get_value() in element_dictionary)
            if is_family:
                families.append(element_dictionary[child_element.get_value()])

        return families

    def get_ancestors(self, individual: IndividualElement) -> List[IndividualElement]:
        """Return elements corresponding to ancestors of an individual
        """
        if not isinstance(individual, IndividualElement):
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag" % python_gedcom_2.tags.GEDCOM_TAG_INDIVIDUAL
            )

        parents = self.get_parents(individual)
        ancestors = []
        ancestors.extend(parents)

        for parent in parents:
            ancestors.extend(self.get_ancestors(parent))

        return ancestors

    def get_parents(self, individual: IndividualElement) -> Tuple[IndividualElement | None, IndividualElement | None]:
        """Return elements corresponding to parents of an individual. (husband, wife)
        """
        if not isinstance(individual, IndividualElement):
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag" % python_gedcom_2.tags.GEDCOM_TAG_INDIVIDUAL
            )

        if not individual.is_child_in_a_family():
            return None, None

        family = self.get_element_by_pointer(individual.get_parent_family_pointer())

        if not isinstance(family, FamilyElement):
            return None, None

        husband: IndividualElement | None = self.get_element_by_pointer(family.get_husband_pointer()) if family.has_husband() else None
        wife: IndividualElement | None = self.get_element_by_pointer(family.get_wife_pointer()) if family.has_wife() else None

        return husband, wife

    def get_children(self, individual: IndividualElement) -> List[IndividualElement]:
        """
        Return a list of children of an individual that are directly related and not adopted.
        """
        if not isinstance(individual, IndividualElement):
            raise NotAnActualIndividualError(
                f"Operation only valid for elements with {python_gedcom_2.tags.GEDCOM_TAG_INDIVIDUAL} tag"
            )

        children: List[IndividualElement] = []
        families = self.get_families(individual, python_gedcom_2.tags.GEDCOM_TAG_FAMILY_SPOUSE)

        for family in families:
            for pointer in family.get_children_pointers():
                child = self.get_element_by_pointer(pointer)
                if isinstance(child, IndividualElement):
                    children.append(child)

        return children

    def get_descendants(self, individual: IndividualElement) -> List[IndividualElement]:
        if not isinstance(individual, IndividualElement):
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag" % python_gedcom_2.tags.GEDCOM_TAG_INDIVIDUAL
            )

        descendants: List[IndividualElement] = []
        families = self.get_families(individual, python_gedcom_2.tags.GEDCOM_TAG_FAMILY_SPOUSE)
        for family in families:
            for pointer in family.get_children_pointers():
                child = self.get_element_by_pointer(pointer)
                if isinstance(child, IndividualElement):
                    descendants.append(child)
                    descendants.extend(self.get_descendants(child))

        return descendants

    def find_path_to_ancestor(self, descendant: IndividualElement, ancestor: IndividualElement, path=None) -> List[IndividualElement] | None:
        """Return path from descendant to ancestor
        """
        if not isinstance(descendant, IndividualElement) or not isinstance(ancestor, IndividualElement):
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag." % python_gedcom_2.tags.GEDCOM_TAG_INDIVIDUAL
            )

        if not path:
            path = [descendant]

        if path[-1].get_pointer() == ancestor.get_pointer():
            return path

        parents = self.get_parents(descendant)
        for parent in parents:
            potential_path = self.find_path_to_ancestor(parent, ancestor, path + [parent])
            if potential_path is not None:
                return potential_path

        return None

    def convert_pointers_to_elements(self, *args, pointers: List[str] | None=None) -> List[Element | None]:
        if pointers is None:
            pointers = []
        pointers.extend(*args)
        return [self.get_element_by_pointer(pointer) for pointer in pointers]

    # Other methods

    def print_gedcom(self):
        """Write GEDCOM data to stdout"""
        self.save_gedcom(stdout)

    def save_gedcom(self, open_file):
        """Save GEDCOM data to a file
        :type open_file: file
        """
        if version_info[0] >= 3:
            open_file.write(self.get_root_element().to_gedcom_string(True))
        else:
            open_file.write(self.get_root_element().to_gedcom_string(True).encode('utf-8-sig'))
