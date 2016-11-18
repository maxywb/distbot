import lxml.etree

def get_xml_text(blob):
    return lxml.etree.tostring(blob, pretty_print=True).decode("utf-8")


