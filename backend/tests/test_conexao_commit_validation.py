"""Unit tests for ConexaoCommitClient form validation logic."""
from app.core.auth.adapters.playwright.trace.commit_trace import FormSnapshot
from app.core.auth.adapters.playwright.clients.conexao_commit import (
    REQUIRED_HIDDEN,
    REQUIRED_LOOKUP_KEYS,
)


def _valid_hidden() -> dict[str, str]:
    return {
        "utf8": "✓",
        "page": "",
        "seg_operador[codoperador]": "1659",
        "lookup_key[seg_operador[codmunicipio]]": "3128253",
        "seg_operador[codmunicipio]": "3128253",
        "lookup_key[seg_operador[codunidade]]": "14",
        "seg_operador[codunidade]": "14",
        "lookup_key[seg_operador[codsetor]]": "10",
        "seg_operador[codsetor]": "10",
    }


def test_required_fields_defined():
    assert "seg_operador[codmunicipio]" in REQUIRED_HIDDEN
    assert "lookup_key[seg_operador[codsetor]]" in REQUIRED_LOOKUP_KEYS


def test_form_snapshot_matches_protocol():
    hidden = _valid_hidden()
    form = FormSnapshot(
        ts="",
        page_url="",
        form_action="/seg/operador/1659/create_conexao",
        form_method="post",
        data_remote="true",
        csrf_meta="token",
        authenticity_token_in_form=None,
        hidden_fields=hidden,
        select2_labels={},
    )
    assert form.authenticity_token_in_form is None
    assert hidden["seg_operador[codunidade]"] == "14"
    assert hidden["lookup_key[seg_operador[codunidade]]"] == "14"
