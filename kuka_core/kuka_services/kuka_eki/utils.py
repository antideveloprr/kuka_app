import xml.etree.ElementTree as elementTree


class XmlTag:
    """

    """
    def __init__(self, title, value, attributes_dict):
        self.title = title
        self.value = value
        self.attributes = attributes_dict


class XmlReader:
    """
    """
    def __init__(self, content):
        self.__content = content

    def get_tag_value(self, title):
        root = elementTree.fromstring(self.__content)
        return root.find(title).text

    def get_attribute_value(self, tag_title, attribute_title):
        root = elementTree.fromstring(self.__content)
        return root.find(tag_title).get(attribute_title)


class XmlWriter:
    """

    """
    def __init__(self, content):
        self.__content = content
        self.__tags = []

    def set_tag(self, title, value, attributes):
        self.__tags.append(XmlTag(title, value, attributes))

    def evaluate(self):
        for tag in self.__tags:
            self.__content = str(self.__content).replace(tag.title, tag.value)
            for attribute_key in tag.attributes.keys():
                self.__content = str(self.__content)\
                    .replace(attribute_key, '\"'+tag.attributes[attribute_key]+'\"')
        return self.__content



