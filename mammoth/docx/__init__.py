import os

from .. import results, lists
from .document_xml import read_document_xml_element
from .content_types_xml import empty_content_types, read_content_types_xml_element
from .relationships_xml import read_relationships_xml_element, Relationships
from .numbering_xml import read_numbering_xml_element, Numbering
from .styles_xml import read_styles_xml_element, Styles
from .notes_xml import create_footnotes_reader, create_endnotes_reader
from .comments_xml import create_comments_reader
from .files import Files
from . import body_xml, office_xml
from ..zips import open_zip


_empty_result = results.success([])


def read(fileobj):
    zip_file = open_zip(fileobj, "r")
    body_readers = _body_readers(getattr(fileobj, "name", None), zip_file)
    
    return results.combine([
        _read_notes(zip_file, body_readers),
        _read_comments(zip_file, body_readers),
    ]).bind(lambda referents:
        _read_document(zip_file, body_readers, notes=referents[0], comments=referents[1])
    )


def _read_notes(zip_file, body_readers):
    read_footnotes_xml = create_footnotes_reader(body_readers("footnotes"))
    footnotes = _try_read_entry_or_default(
        zip_file, "word/footnotes.xml", read_footnotes_xml, default=_empty_result)
    
    read_endnotes_xml = create_endnotes_reader(body_readers("endnotes"))
    endnotes = _try_read_entry_or_default(
        zip_file, "word/endnotes.xml", read_endnotes_xml, default=_empty_result)
    
    return results.combine([footnotes, endnotes]).map(lists.flatten)


def _read_comments(zip_file, body_readers):
    return _try_read_entry_or_default(
        zip_file,
        "word/comments.xml",
        create_comments_reader(body_readers("comments")),
        default=_empty_result,
    )

    
def _read_document(zip_file, body_readers, notes, comments):
    package_relationships = _try_read_entry_or_default(
        zip_file,
        "_rels/.rels",
        read_relationships_xml_element,
        default=Relationships.EMPTY,
    )
    
    document_filename = _find_document_filename(zip_file, package_relationships)
    
    with zip_file.open(document_filename) as document_fileobj:
        document_xml = office_xml.read(document_fileobj)
        return read_document_xml_element(
            document_xml,
            body_reader=body_readers("document"),
            notes=notes,
            comments=comments,
        )


def _find_document_filename(zip_file, relationships):
    office_document_type = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    targets = [
        target.lstrip("/")
        for target in relationships.find_targets_by_type(office_document_type)
    ] + ["word/document.xml"]
    valid_targets = list(filter(lambda target: zip_file.exists(target), targets))
    if len(valid_targets) == 0:
        return None
    else:
        return valid_targets[0]


def _body_readers(document_path, zip_file):
    content_types = _try_read_entry_or_default(
        zip_file,
        "[Content_Types].xml",
        read_content_types_xml_element,
        empty_content_types,
    )

    numbering = _try_read_entry_or_default(
        zip_file, "word/numbering.xml", read_numbering_xml_element, default=Numbering({}))
    
    styles = _try_read_entry_or_default(
        zip_file,
        "word/styles.xml",
        read_styles_xml_element,
        Styles.EMPTY,
    )
    
    def for_name(name):
        relationships_path = "word/_rels/{0}.xml.rels".format(name)
        relationships = _try_read_entry_or_default(
            zip_file, relationships_path, read_relationships_xml_element,
            default=Relationships.EMPTY)
            
        return body_xml.reader(
            numbering=numbering,
            content_types=content_types,
            relationships=relationships,
            styles=styles,
            docx_file=zip_file,
            files=Files(None if document_path is None else os.path.dirname(document_path)),
        )
    
    return for_name


def _try_read_entry_or_default(zip_file, name, reader, default):
    if zip_file.exists(name):
        with zip_file.open(name) as fileobj:
            return reader(office_xml.read(fileobj))
    else:
        return default
