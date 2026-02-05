from pygls.lsp.server import LanguageServer
from lsprotocol.types import (
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_SAVE,
    DidOpenTextDocumentParams,
    DidChangeTextDocumentParams,
    DidSaveTextDocumentParams,
    Diagnostic,
    PublishDiagnosticsParams,
)
from htpy_lsp.validator import validate_document

import logging
import os

# Create a log file in the project directory
LOG_FILE = "/Users/cali/Developmet/lsp-htpy-python/lsp.log"
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, filemode='w')

server = LanguageServer("htpy-lsp", "v0.1.0")

@server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: LanguageServer, params: DidOpenTextDocumentParams):
    logging.debug(f"did_open: {params.text_document.uri}")
    doc = ls.workspace.get_text_document(params.text_document.uri)
    diagnostics = validate_document(doc)
    logging.debug(f"found {len(diagnostics)} diagnostics")
    ls.text_document_publish_diagnostics(
        PublishDiagnosticsParams(uri=params.text_document.uri, diagnostics=diagnostics)
    )

@server.feature(TEXT_DOCUMENT_DID_CHANGE)
async def did_change(ls: LanguageServer, params: DidChangeTextDocumentParams):
    logging.debug(f"did_change: {params.text_document.uri}")
    doc = ls.workspace.get_text_document(params.text_document.uri)
    diagnostics = validate_document(doc)
    logging.debug(f"found {len(diagnostics)} diagnostics")
    ls.text_document_publish_diagnostics(
        PublishDiagnosticsParams(uri=params.text_document.uri, diagnostics=diagnostics)
    )

@server.feature(TEXT_DOCUMENT_DID_SAVE)
async def did_save(ls: LanguageServer, params: DidSaveTextDocumentParams):
    logging.debug(f"did_save: {params.text_document.uri}")
    doc = ls.workspace.get_text_document(params.text_document.uri)
    diagnostics = validate_document(doc)
    logging.debug(f"found {len(diagnostics)} diagnostics")
    ls.text_document_publish_diagnostics(
        PublishDiagnosticsParams(uri=params.text_document.uri, diagnostics=diagnostics)
    )

def main():
    server.start_io()

if __name__ == "__main__":
    main()
