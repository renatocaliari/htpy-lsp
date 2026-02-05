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

server = LanguageServer("htpy-lsp", "v0.1.0")

@server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: LanguageServer, params: DidOpenTextDocumentParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    diagnostics = validate_document(doc)
    ls.text_document_publish_diagnostics(
        PublishDiagnosticsParams(uri=params.text_document.uri, diagnostics=diagnostics)
    )

@server.feature(TEXT_DOCUMENT_DID_CHANGE)
async def did_change(ls: LanguageServer, params: DidChangeTextDocumentParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    diagnostics = validate_document(doc)
    ls.text_document_publish_diagnostics(
        PublishDiagnosticsParams(uri=params.text_document.uri, diagnostics=diagnostics)
    )

@server.feature(TEXT_DOCUMENT_DID_SAVE)
async def did_save(ls: LanguageServer, params: DidSaveTextDocumentParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    diagnostics = validate_document(doc)
    ls.text_document_publish_diagnostics(
        PublishDiagnosticsParams(uri=params.text_document.uri, diagnostics=diagnostics)
    )

def main():
    server.start_io()

if __name__ == "__main__":
    main()
